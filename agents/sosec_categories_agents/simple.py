import multiprocessing

def worker():
    print("Worker process")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    multiprocessing.set_start_method("spawn", force=True)
    p = multiprocessing.Process(target=worker)
    p.start()
    p.join()
    print("Main process")
