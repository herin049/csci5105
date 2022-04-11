exception FileNotFound {
}

service CoordinatorService {
    void write(1:string file_name, 2:string content);
    string read(1:string file_name) throws (1:FileNotFound error);
}

service ServerService {
    void write(1:string file_name, 2:string content);
    string read(1:string file_name) throws (1:FileNotFound error);
    i32 get_version(1:string file_name);
    void update(1:string file_name, 2:i32 version, 3:string content);
    string fetch(1:string file_name) throws (1:FileNotFound error);
}