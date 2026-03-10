from utils import save_config

def run(args):
    """Handles the connection command to set the server URL."""
    if not args:
        print("Usage: xtc connect @<server_url>")
        return
    
    # We strip the '@' if the user provides it, but allow raw URL as well
    server_url = args[0].replace("@", "")
    save_config(server_url)