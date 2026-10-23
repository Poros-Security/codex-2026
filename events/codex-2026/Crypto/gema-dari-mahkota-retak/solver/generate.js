#!/usr/bin/env node

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const ROOT = path.resolve(__dirname, "..");
const OUTPUT = path.join(ROOT, "src", "challenge.json");
const HANDOUT = path.join(ROOT, "dist", "handout.zip");
const FLAG = "CODEX26{r3t4k4n_m3mb0c0rk4n_m4hk0t4}";
const SIGNATURE_COUNT = 64;

function fromBase64Url(value) {
  const bytes = Buffer.from(value, "base64url");
  return bytes.length === 0 ? 0n : BigInt(`0x${bytes.toString("hex")}`);
}

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

function gcd(a, b) {
  let x = a < 0n ? -a : a;
  let y = b < 0n ? -b : b;
  while (y !== 0n) [x, y] = [y, x % y];
  return x;
}

function hex(value) {
  return value.toString(16);
}

function representative(message) {
  return fromBuffer(crypto.createHash("sha256").update(message, "utf8").digest());
}

function crtSignature(messageInteger, key, faultyPBranch = false) {
  let sp = modPow(messageInteger, key.dp, key.p);
  const sq = modPow(messageInteger, key.dq, key.q);
  if (faultyPBranch) {
    const fault = 1n + fromBuffer(crypto.randomBytes(3));
    sp = mod(sp + fault, key.p);
  }
  const h = mod(key.qInv * (sp - sq), key.p);
  return mod(sq + key.q * h, key.n);
}

function randomIndex(limit) {
  return crypto.randomBytes(2).readUInt16BE(0) % limit;
}

function main() {
  const { privateKey } = crypto.generateKeyPairSync("rsa", {
    modulusLength: 1024,
    publicExponent: 0x10001,
  });
  const jwk = privateKey.export({ format: "jwk" });
  const key = {
    n: fromBase64Url(jwk.n),
    e: fromBase64Url(jwk.e),
    p: fromBase64Url(jwk.p),
    q: fromBase64Url(jwk.q),
    dp: fromBase64Url(jwk.dp),
    dq: fromBase64Url(jwk.dq),
    qInv: fromBase64Url(jwk.qi),
  };

  const faultIndex = randomIndex(SIGNATURE_COUNT);
  let decoyIndex = randomIndex(SIGNATURE_COUNT);
  while (decoyIndex === faultIndex) decoyIndex = randomIndex(SIGNATURE_COUNT);

  const signatures = [];
  for (let index = 0; index < SIGNATURE_COUNT; index += 1) {
    const message = `audit:${index.toString().padStart(2, "0")}:${crypto.randomBytes(12).toString("hex")}`;
    const m = representative(message);
    let signature = crtSignature(m, key, index === faultIndex);

    if (index === decoyIndex) {
      let candidate = mod(signature ^ 1n, key.n);
      while (gcd(modPow(candidate, key.e, key.n) - m, key.n) !== 1n) {
        candidate = mod(candidate + 1n, key.n);
      }
      signature = candidate;
    }

    signatures.push({ id: index, message, signature: hex(signature) });
  }

  const flagInteger = fromBuffer(Buffer.from(FLAG, "utf8"));
  if (flagInteger >= key.n) throw new Error("Flag does not fit in the RSA modulus");
  const ciphertext = modPow(flagInteger, key.e, key.n);

  const output = {
    title: "Gema dari Mahkota Retak",
    public_key: { n: hex(key.n), e: hex(key.e) },
    signature_scheme: "RSA textbook atas bilangan big-endian SHA-256(pesan)",
    ciphertext_scheme: "RSA textbook atas bilangan big-endian plaintext UTF-8",
    ciphertext: hex(ciphertext),
    signatures,
  };

  fs.mkdirSync(path.dirname(OUTPUT), { recursive: true });
  fs.mkdirSync(path.dirname(HANDOUT), { recursive: true });
  fs.writeFileSync(OUTPUT, `${JSON.stringify(output, null, 2)}\n`, "utf8");

  const bad = signatures.filter((entry) => {
    const verified = modPow(BigInt(`0x${entry.signature}`), key.e, key.n);
    return verified !== representative(entry.message);
  });
  if (bad.length !== 2) throw new Error(`Expected two invalid signatures, found ${bad.length}`);

  const useful = bad.filter((entry) => {
    const verified = modPow(BigInt(`0x${entry.signature}`), key.e, key.n);
    const factor = gcd(verified - representative(entry.message), key.n);
    return factor > 1n && factor < key.n;
  });
  if (useful.length !== 1) throw new Error(`Expected one exploitable signature, found ${useful.length}`);

  if (fs.existsSync(HANDOUT)) fs.unlinkSync(HANDOUT);
  const handoutSrc = path.join(ROOT, "handout_src");
  fs.mkdirSync(handoutSrc, { recursive: true });
  const hsChallenge = path.join(handoutSrc, "challenge.json");
  fs.copyFileSync(OUTPUT, hsChallenge);
  const redacted = path.join(handoutSrc, "generate_gema_dari_mahkota_retak.js");
  const zipScript = `
import zipfile
z = zipfile.ZipFile(r'''${HANDOUT.replace(/\\/g, "\\\\")}''', "w", compression=zipfile.ZIP_DEFLATED)
z.write(r'''${hsChallenge.replace(/\\/g, "\\\\")}''', arcname="challenge.json")
z.write(r'''${redacted.replace(/\\/g, "\\\\")}''', arcname="generate_gema_dari_mahkota_retak.js")
z.close()
`;
  const zipped = spawnSync("python", ["-c", zipScript], { encoding: "utf8" });
  if (zipped.status !== 0) {
    throw new Error(`failed to build handout.zip: ${zipped.stderr || zipped.stdout}`);
  }

  console.log(`[+] Wrote ${OUTPUT}`);
  console.log(`[+] Wrote ${HANDOUT}`);
  console.log(`[+] Audit entries: ${SIGNATURE_COUNT}`);
  console.log(`[+] Invalid signatures: ${bad.length}; exploitable CRT faults: ${useful.length}`);
}

main();
