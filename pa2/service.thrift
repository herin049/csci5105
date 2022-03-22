exception DHTBusy {
}

exception WordNotFound {
}

exception DuplicateWord {
}

struct NodeInfo {
    1: i64 id;
    2: string ip;
    3: i16 port;
}

service SuperNodeService {
    NodeInfo get_join_node(1:string ip, 2:i16 port) throws (1:DHTBusy error);
    void post_join();
    NodeInfo get_node_for_client();
}

service ChordNodeService {
    void put(1:string word, 2:string definition) throws(1:DuplicateWord error);
    string get(1:string word) throws (1:WordNotFound error);
    NodeInfo find_successor(1:i64 key);
    NodeInfo get_predecessor();
    void update_predecessor(1:NodeInfo new_predecessor);
    void update_finger_table(1:NodeInfo new_node, 2:i64 index);
}