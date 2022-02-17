import org.apache.thrift.server.TServer;
import org.apache.thrift.server.TServer.Args;
import org.apache.thrift.server.TSimpleServer;
import org.apache.thrift.transport.TSSLTransportFactory;
import org.apache.thrift.transport.TSSLTransportFactory.TSSLTransportParameters;
import org.apache.thrift.transport.TServerSocket;
import org.apache.thrift.transport.TServerTransport;

import thrift_service.KeyValueStore;

public class Server {
    public static KeyValueStoreHandler handler;

    public static KeyValueStore.Processor processor;

    public static void main(String [] args) {
        try {
            handler = new KeyValueStoreHandler();
            processor = new KeyValueStore.Processor(handler);

            Runnable unsecure = new Runnable() {
                public void run() {
                    unsecure(processor);
                }
            };
            Runnable secure = new Runnable() {
                public void run() {
                    secure(processor);
                }
            };

            new Thread(unsecure).start();
            new Thread(secure).start();
        } catch (Exception x) {
            x.printStackTrace();
        }
    }

    public static void unsecure(KeyValueStore.Processor processor) {
        try {
            TServerTransport serverTransport = new TServerSocket(Shared.UNSECURE_PORT);
            TServer server = new TSimpleServer(new Args(serverTransport).processor(processor));

            System.out.format("Starting unsecure server on port %d\n", Shared.UNSECURE_PORT);
            server.serve();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void secure(KeyValueStore.Processor processor) {
        try {
            TSSLTransportParameters params = new TSSLTransportParameters();
            params.setKeyStore("../thrift/lib/java/test/.keystore", "thrift", null, null);

            TServerTransport serverTransport = TSSLTransportFactory.getServerSocket(Shared.SECURE_PORT, 0, null, params);
            TServer server = new TSimpleServer(new Args(serverTransport).processor(processor));

            System.out.format("Starting secure server on port %d\n", Shared.SECURE_PORT);
            server.serve();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
