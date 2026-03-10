import sys
from commands import connect, create, delete, chat

def main():
    if len(sys.argv) < 2:
        print("Usage: xtc <command> [args]")
        return

    cmd = sys.argv[1]

    # Dispatching
    if cmd == "connect":
        connect.run(sys.argv[2:])
    elif cmd == "create:room":
        create.run(sys.argv[2:])
    elif cmd == "delete:room":
        delete.run(sys.argv[2:])
    elif cmd == "start:chat":
        chat.run(sys.argv[2:])
    else:
        print("Unknown command.")

if __name__ == "__main__":
    main()