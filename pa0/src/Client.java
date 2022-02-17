import org.apache.thrift.TException;
import org.apache.thrift.transport.TSSLTransportFactory;
import org.apache.thrift.transport.TTransport;
import org.apache.thrift.transport.TSocket;
import org.apache.thrift.transport.TSSLTransportFactory.TSSLTransportParameters;
import org.apache.thrift.protocol.TBinaryProtocol;
import org.apache.thrift.protocol.TProtocol;

import thrift_service.*;

public class Client {
    public static void main(String [] args) {

        if (args.length != 1) {
            System.out.println("Please enter 'unsecure' or 'secure'");
            System.exit(0);
        }

        try {
            TTransport transport;
            if (args[0].contains("unsecure")) {
                transport = new TSocket("localhost", Shared.UNSECURE_PORT);
                transport.open();
            } else {
                TSSLTransportParameters params = new TSSLTransportParameters();
                params.setTrustStore("../thrift/lib/java/test/.truststore", "thrift", "SunX509", "JKS");
                transport = TSSLTransportFactory.getClientSocket("localhost", Shared.SECURE_PORT, 0, params);
            }

            TProtocol protocol = new  TBinaryProtocol(transport);
            KeyValueStore.Client client = new KeyValueStore.Client(protocol);

            perform(client);

            transport.close();
        } catch (TException x) {
            x.printStackTrace();
        }
    }

    private static void perform(KeyValueStore.Client client) throws TException
    {
        try {
            String foo = client.get("foo");
            System.out.format("\"foo\" -> \"%s\"\n", foo);
        } catch (InvalidOperation exception) {
            System.out.format("Invalid operation: \"%s\"\n", exception.why);
        }

        client.put("bar", "car");
        client.put("baz", "green");
        client.put("baz", "red");

        try {
            String bar = client.get("bar");
            System.out.format("\"bar\" -> \"%s\"\n", bar);
        } catch (InvalidOperation exception) {
            System.out.format("Invalid operation: \"%s\"\n", exception.why);
        }

        try {
            String baz = client.get("baz");
            System.out.format("\"baz\" -> \"%s\"\n", baz);
        } catch (InvalidOperation exception) {
            System.out.format("Invalid operation: \"%s\"\n", exception.why);
        }

        try {
            String foo = client.get("foo");
            System.out.format("\"foo\" -> \"%s\"\n", foo);
        } catch (InvalidOperation exception) {
            System.out.format("Invalid operation: \"%s\"\n", exception.why);
        }
    }
}