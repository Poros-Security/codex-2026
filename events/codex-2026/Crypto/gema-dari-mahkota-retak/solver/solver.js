#!/usr/bin/env node

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const CHALLENGE = path.resolve(__dirname, "..", "src", "challenge.json");

function fromBuffer(value) {
  return value.length === 0 ? 0n : BigInt(`0x${value.toString("hex")}`);
}

function mod(value, modulus) {
  const result = value % modulus;
  return result >= 0n ? result : result + modulus;
}

function modPow(base, exponent, modulus) {
  let result = 1n;
  let current = mod(base, modulus);
  let power = exponent;
  while (power > 0n) {
    if (power & 1n) result = (result * current) % modulus;
    current = (current * current) % modulus;
    power >>= 1n;
  }
  return result;
}

function extendedGcd(a, b) {
  if (b === 0n) return [a, 1n, 0n];
  const [g, x1, y1] = extendedGcd(b, a % b);
  return [g, y1, x1 - (a / b) * y1];
}

function inverse(value, modulus) {
  const [g, x] = extendedGcd(mod(value, modulus), modulus);
  if (g !== 1n) throw new Error("Inverse does not exist");
  return mod(x, modulus);
}

function gcd(a, b) {
  let x = a < 0n ? -a : a;
  let y = b < 0n ? -b : b;
  while (y !== 0n) [x, y] = [y, x % y];
  return x;
}

function representative(message) {
  return fromBuffer(crypto.createHash("sha256").update(message, "utf8").digest());
}

function toBuffer(value) {
  let encoded = value.toString(16);
  if (encoded.length % 2 !== 0) encoded = `0${encoded}`;
  return Buffer.from(encoded, "hex");
}

function main() {
  const challenge = JSON.parse(fs.readFileSync(CHALLENGE, "utf8"));
  const n = BigInt(`0x${challenge.public_key.n}`);
  const e = BigInt(`0x${challenge.public_key.e}`);
  let factor = null;

  for (const entry of challenge.signatures) {
    const message = representative(entry.message);
    const signature = BigInt(`0x${entry.signature}`);
    const verified = modPow(signature, e, n);
    if (verified === message) continue;

    const candidate = gcd(verified - message, n);
    console.log(`[*] Invalid signature ${entry.id}: gcd has ${candidate.toString(2).length} bits`);
    if (candidate > 1n && candidate < n) {
      factor = candidate;
      console.log(`[+] Signature ${entry.id} contains an exploitable CRT fault`);
      break;
    }
  }

  if (factor === null) throw new Error("No exploitable signature found");
  const otherFactor = n / factor;
  if (factor * otherFactor !== n) throw new Error("Factorization failed");

  const phi = (factor - 1n) * (otherFactor - 1n);
  const d = inverse(e, phi);
  const ciphertext = BigInt(`0x${challenge.ciphertext}`);
  const plaintext = toBuffer(modPow(ciphertext, d, n)).toString("utf8");
  const match = plaintext.match(/CODEX26\{[A-Za-z0-9_]+\}/);
  if (!match) throw new Error(`Decryption produced unexpected plaintext: ${plaintext}`);

  console.log(`[+] Factored the ${n.toString(2).length}-bit RSA modulus`);
  console.log(`[+] Recovered flag: ${match[0]}`);
}

main();
