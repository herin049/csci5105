import thrift_service.InvalidOperation;
import thrift_service.KeyValueStore;

import java.util.HashMap;
import java.util.Map;

public class KeyValueStoreHandler implements KeyValueStore.Iface {
    private final Map<String, String> keyValueMap;

    public KeyValueStoreHandler() {
        keyValueMap = new HashMap<>();
    }

    @Override
    public String get(String key) throws InvalidOperation {
        String value = keyValueMap.get(key);
        if (value != null) return value;
        throw new InvalidOperation("Key not found in store.");
    }

    @Override
    public void put(String key, String value) {
        keyValueMap.put(key, value);
    }
}