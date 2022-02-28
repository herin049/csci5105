exception TaskRejected {
    1: string why
}

struct Task {
    1: string data_dir;
    2: string file_name;
}

struct Job {
    1: string data_dir;
    2: list<string> file_names;
}

service ServerService {
    double process(1:Job job)
}

service ComputeService {
    void process(1:Task task) throws (1:TaskRejected error)
}