import psutil
import os
import signal

def kill_on_ports(ports):
    print(f"Aggressively checking ports: {ports}")
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            conns = proc.connections(kind='inet')
            for conn in conns:
                if conn.laddr.port in ports:
                    print(f"Found process {proc.info['name']} (PID: {proc.info['pid']}) on port {conn.laddr.port}")
                    try:
                        os.kill(proc.info['pid'], signal.SIGTERM)
                        print(f"Sent SIGTERM to {proc.info['pid']}")
                    except:
                        os.kill(proc.info['pid'], signal.SIGKILL)
                        print(f"Sent SIGKILL to {proc.info['pid']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

if __name__ == "__main__":
    kill_on_ports([8000, 3000])
    print("Done.")
