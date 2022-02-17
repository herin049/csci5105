exception TaskRejected {
    1: string why
}

struct Task {
    1: string file_name
}

struct Job {
    1: list<string> file_names
}

service ServerService {
    i32 process(1:Job job)
}

service ComputeService {
    void process(1:Task task) throws (1:TaskRejected error)
}