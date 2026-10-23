import java.util.Base64;

public class Chall {
    private static final int    FLAG_LEN = 43;
    private static final String TARGET   = "QCB4cJjL64HjyfvzGaBB+ynzoPvJw6Ax+3nDoOPboEnDoPPD+8lBGcN5sQ==";

    private static boolean check(String input) {
        byte[] in = input.getBytes(java.nio.charset.StandardCharsets.UTF_8);
        if (in.length != FLAG_LEN) return false;
        byte[] out = new byte[in.length];
        for (int i = 0; i < in.length; i++) {
            int b = in[i] & 0xFF;
            int t = ((b << 3) | (b >>> 5)) & 0xFF;
            t ^= 0x5A;
            out[i] = (byte) t;
        }
        return Base64.getEncoder().encodeToString(out).equals(TARGET);
    }

    public static void main(String[] args) {
        if (args.length != 1) {
            System.out.println("[-] Access denied.");
            System.exit(1);
        }
        if (check(args[0])) {
            System.out.println("[+] Access granted! Flag verified: " + args[0]);
            System.exit(0);
        }
        System.out.println("[-] Access denied.");
        System.exit(1);
    }
}