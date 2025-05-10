import subprocess
import gradio as gr

def ping(address, count):
    try:
        result = subprocess.run(
            ["ping", "-n", str(int(count)), address],
            capture_output=True,
            text=True,
            shell=False
        )
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error: {e}"


def traceroute(address):
    try:
        result = subprocess.run(
            ["tracert", address],
            capture_output=True,
            text=True,
            shell=False
        )
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error: {e}"


def network_tool(address, count, action):
    if action == "Ping":
        return ping(address, count)
    return traceroute(address)


def main():
    iface = gr.Interface(
        fn=network_tool,
        inputs=[
            gr.Textbox(label="Target Address", placeholder="e.g. 8.8.8.8"),
            gr.Number(label="Ping Count", value=4, precision=0),
            gr.Radio(["Ping", "Traceroute"], label="Action")
        ],
        outputs=gr.Textbox(label="Results"),
        title="Simple Ping & Traceroute Tool",
        description="Choose Ping to send ICMP echoes or Traceroute to map the route to the target."
    )
    iface.launch(share=False)

if __name__ == "__main__":
    main()
