import requests
import openai
import json
import os
import gradio as gr

openai.api_key = os.getenv('OPENAI_API_KEY')

vcsa_manage_api_url = os.getenv('VCENTER_API_MANAGEE_URL')

def parse_user_command(user_input):
    try:
        api_description = """
        You are an assistant for managing virtual machines via a vCenter API.
        The API supports the following actions:
        - "list_vms": Lists all virtual machines. No parameters are required.
        - "get_vm_details": Gets details of a specific virtual machine. Required parameter: vm_name (string).
        - "manage_power": Manages the power state of a virtual machine. Required parameters:
          - vm_name (string): Name of the virtual machine.
          - operation (string): One of "start", "shutdown", "restart", or "poweroff".
        Respond with a Python dictionary that specifies the action and its parameters.
        """

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": api_description},
                {"role": "user", "content": user_input}
            ]
        )

        ai_response = response.choices[0].message.content
        try:
            return json.loads(ai_response)
        except json.JSONDecodeError:

            return {"non_json_response": ai_response}
    except openai.OpenAIError as e:
        return {"error": f"OpenAI API error: {str(e)}"}
    except Exception as e:
        return {"error": f"General error: {str(e)}"}

def enhance_response_with_ai(original_input, parsed_command, vcenter_response):
    try:
        enhancement_prompt = """
        You are an assistant enhancing responses for a virtual machine management system.
        Based on the following details, generate a clear and friendly summary:
        - User Input: {user_input}
        - Parsed Command: {parsed_command}
        - vCenter API Response: {vcenter_response}
        Ensure the response is concise and helpful for the user.
        """.format(
            user_input=original_input,
            parsed_command=json.dumps(parsed_command, indent=2),
            vcenter_response=json.dumps(vcenter_response, indent=2)
        )
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": enhancement_prompt}
            ]
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"Error enhancing response with AI: {str(e)}"

def execute_vcenter_operation(parsed_command):
    try:
        action = parsed_command.get("action")

        if action == "list_vms":
            response = requests.get(f"{vcsa_manage_api_url}/vms")
        elif action == "get_vm_details":
            vm_name = parsed_command.get("vm_name")
            response = requests.get(f"{vcsa_manage_api_url}/vm_details", params={"vm_name": vm_name})
        elif action == "manage_power":
            payload = {
                "vm_name": parsed_command.get("vm_name"),
                "operation": parsed_command.get("operation")
            }
            response = requests.post(f"{vcsa_manage_api_url}/vms/power", json=payload)
        else:
            return {"error": "Invalid action"}

        return response.json()
    except requests.RequestException as e:
        return {"error": f"HTTP request error: {str(e)}"}
    except Exception as e:
        return {"error": f"General error: {str(e)}"}

def chatbot_interface(user_input, history):
    parsed_command = parse_user_command(user_input)

    if "non_json_response" in parsed_command:
        return f"AI Response: {parsed_command['non_json_response']}"

    if "error" in parsed_command:
        return f"Error: {parsed_command['error']}"

    vcenter_response = execute_vcenter_operation(parsed_command)
    enhanced_response = enhance_response_with_ai(user_input, parsed_command, vcenter_response)

    return enhanced_response

app = gr.ChatInterface(
    fn=chatbot_interface
)

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=8000)