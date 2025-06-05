from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
import json
import os
import subprocess
import threading
import time
import signal
import sys

load_dotenv()

client = OpenAI()

class EnhancedAssistant:
    def __init__(self):
        self.running_processes = []
        self.project_config = {}
        
    def run_command(self, cmd: str):
        """Execute shell command and return output"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": "Command timed out after 30 seconds"
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def run_server(self, cmd: str):
        """Run server command in background"""
        try:
            process = subprocess.Popen(cmd, shell=True)
            self.running_processes.append(process)
            return {
                "returncode": 0,
                "stdout": f"Server started with PID: {process.pid}",
                "stderr": ""
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def stop_servers(self):
        """Stop all running servers"""
        for process in self.running_processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
        self.running_processes.clear()
        return {
            "returncode": 0,
            "stdout": "All servers stopped",
            "stderr": ""
        }
    
    def get_project_preferences(self):
        """Get user preferences for CSS framework and project type"""
        print("\n🎨 Project Setup Preferences:")
        
        # CSS Framework choice
        print("\nChoose CSS Framework:")
        print("1. Tailwind CSS")
        print("2. Bootstrap")
        print("3. None (Plain CSS)")
        
        while True:
            choice = input("Enter choice (1-3): ").strip()
            if choice == "1":
                self.project_config['css_framework'] = 'tailwind'
                break
            elif choice == "2":
                self.project_config['css_framework'] = 'bootstrap'
                break
            elif choice == "3":
                self.project_config['css_framework'] = 'none'
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
        
        # Project type
        print("\nChoose Project Type:")
        print("1. React")
        print("2. Vue")
        print("3. Next.js")
        print("4. HTML/CSS/JS")
        print("5. Node.js/Express")
        
        while True:
            choice = input("Enter choice (1-5): ").strip()
            if choice == "1":
                self.project_config['project_type'] = 'react'
                break
            elif choice == "2":
                self.project_config['project_type'] = 'vue'
                break
            elif choice == "3":
                self.project_config['project_type'] = 'nextjs'
                break
            elif choice == "4":
                self.project_config['project_type'] = 'html'
                break
            elif choice == "5":
                self.project_config['project_type'] = 'nodejs'
                break
            else:
                print("Invalid choice. Please enter 1-5.")
        
        return self.project_config

available_tools = {
    "run_command": None,  # Will be set later
    "run_server": None,   # Will be set later
    "stop_servers": None, # Will be set later
    "get_project_preferences": None  # Will be set later
}

SYSTEM_PROMPT = f"""
You are an advanced AI Assistant specialized in web development and shell commands.
You work in start, plan, action, observe mode with enhanced capabilities.

ENHANCED CAPABILITIES:
- Project setup with CSS framework preferences (Tailwind CSS, Bootstrap, or None)
- Support for React, Vue, Next.js, HTML/CSS/JS, and Node.js projects
- Server management (start/stop development servers)
- Automatic dependency installation
- Smart project structure creation
- Real-time development workflow

WORKFLOW:
1. For new projects: Ask for preferences using get_project_preferences
2. Plan the step-by-step execution
3. Execute actions using available tools
4. Observe results and continue or resolve

RULES:
- Always follow the Output JSON Format
- Perform one step at a time and wait for observation
- For web projects, automatically set up the chosen CSS framework
- When starting servers, use run_server instead of run_command
- Handle errors gracefully and provide solutions
- Don't ask for user input during command execution

OUTPUT JSON FORMAT:
{{
    "step": "plan|action|observe|output",
    "content": "Detailed description of what you're doing",
    "function": "Function name if step is action",
    "input": "Function input parameter"
}}

AVAILABLE TOOLS:
- "run_command": Execute shell commands (ls, mkdir, npm install, etc.)
- "run_server": Start development servers in background (npm start, python -m http.server, etc.)
- "stop_servers": Stop all running development servers
- "get_project_preferences": Get user preferences for CSS framework and project type

PROJECT SETUP EXAMPLES:
- React + Tailwind: npx create-react-app myapp && cd myapp && npm install -D tailwindcss postcss autoprefixer
- Vue + Bootstrap: npm create vue@latest myapp && cd myapp && npm install bootstrap
- Next.js + Tailwind: npx create-next-app@latest myapp --tailwind
- HTML + Bootstrap: Create index.html with Bootstrap CDN

COMMON WORKFLOWS:
1. Create project structure
2. Install dependencies
3. Set up CSS framework
4. Create sample files
5. Start development server
6. Provide next steps

Remember: Be proactive in setting up complete development environments!
"""

def signal_handler(sig, frame):
    print('\n\n🛑 Shutting down gracefully...')
    assistant.stop_servers()
    sys.exit(0)

def main():
    global assistant
    assistant = EnhancedAssistant()
    
    # Set up tool references
    available_tools["run_command"] = assistant.run_command
    available_tools["run_server"] = assistant.run_server
    available_tools["stop_servers"] = assistant.stop_servers
    available_tools["get_project_preferences"] = assistant.get_project_preferences
    
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, signal_handler)
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    
    print("🚀 Enhanced AI Development Assistant")
    print("Type 'exit' to quit, 'stop' to stop all servers")
    print("=" * 50)
    
    while True:
        try:
            query = input("\n> ").strip()
            
            if query.lower() in ['exit', 'quit']:
                assistant.stop_servers()
                print("👋 Goodbye!")
                break
            
            if query.lower() == 'stop':
                result = assistant.stop_servers()
                print(f"🛑 {result['stdout']}")
                continue
            
            if not query:
                continue
            
            messages.append({"role": "user", "content": query})
            
            step_count = 0
            max_steps = 20  # Prevent infinite loops
            
            while step_count < max_steps:
                try:
                    response = client.chat.completions.create(
                        model="gpt-4.1",
                        response_format={"type": "json_object"},
                        messages=messages,
                        temperature=0.1
                    )
                    
                    assistant_message = response.choices[0].message.content
                    messages.append({"role": "assistant", "content": assistant_message})
                    
                    try:
                        parsed_response = json.loads(assistant_message)
                    except json.JSONDecodeError:
                        print("❌ Error: Invalid JSON response from AI")
                        break
                    
                    step = parsed_response.get("step", "")
                    content = parsed_response.get("content", "")
                    
                    if step == "plan":
                        print(f"🧠 Planning: {content}")
                        step_count += 1
                        continue
                    
                    elif step == "action":
                        function_name = parsed_response.get("function")
                        function_input = parsed_response.get("input", "")
                        
                        print(f"🛠️  Executing: {function_name}")
                        if content:
                            print(f"   {content}")
                        
                        if function_name in available_tools:
                            if function_name == "get_project_preferences":
                                output = available_tools[function_name]()
                            else:
                                output = available_tools[function_name](function_input)
                            
                            # Format output for AI
                            observation = {
                                "step": "observe",
                                "output": output
                            }
                            messages.append({"role": "user", "content": json.dumps(observation)})
                            
                            # Show user the result
                            if isinstance(output, dict):
                                if output.get("returncode") == 0:
                                    if output.get("stdout"):
                                        print(f"✅ Success: {output['stdout']}")
                                else:
                                    print(f"❌ Error: {output.get('stderr', 'Unknown error')}")
                            else:
                                print(f"ℹ️  Result: {output}")
                        else:
                            print(f"❌ Unknown function: {function_name}")
                            break
                        
                        step_count += 1
                        continue
                    
                    elif step == "output":
                        print(f"🤖 Result: {content}")
                        break
                    
                    elif step == "observe":
                        # AI is processing observation
                        step_count += 1
                        continue
                    
                    else:
                        print(f"❓ Unknown step: {step}")
                        break
                
                except Exception as e:
                    print(f"❌ Error during execution: {str(e)}")
                    break
            
            if step_count >= max_steps:
                print("⚠️  Maximum steps reached. Task may be too complex.")
        
        except KeyboardInterrupt:
            assistant.stop_servers()
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()