namespace java thrift_service

/* Invalid operation exception returns a string indicating why the operation is invalid */
exception InvalidOperation {
  1: string why
}
/* Key-value store service */
service KeyValueStore {
    /* Retrieves the value associated with a given key. Throws an InvalidOperation error if the
       key is not present in the store. */
    string get(1:string key) throws (1:InvalidOperation error),

    /* Inserts a key-value pair into the store. */
    void put(1:string key, 2:string value)
}