"""
Judge0 code execution service + local fallback.

Submits student code + test cases to the Judge0 CE API, compares output
against expected values, and returns a pass rate (0–100).

v2.1: Added local Python execution fallback when Judge0 is unavailable.
v2.2: Added local C++ execution fallback (g++) and C++ auto-wrapping
      for LeetCode-style class Solution submissions.
"""

import os
import sys
import base64
import time
import subprocess
import tempfile
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Language ID mapping (Judge0 v13+)
# ---------------------------------------------------------------------------

LANGUAGE_MAP = {
    "python": 71,    # Python 3
    "cpp": 54,       # C++ (GCC 9.2)
    "java": 62,      # Java (OpenJDK 13)
    "javascript": 63, # JavaScript (Node.js 12)
}


class Judge0Service:
    """Interface to the Judge0 code execution API with local fallback."""

    def __init__(self):
        self.api_url = os.getenv("JUDGE0_API_URL", "https://ce.judge0.com")
        self.api_key = os.getenv("JUDGE0_API_KEY", "")
        self.timeout = int(os.getenv("JUDGE0_TIMEOUT", "15"))
        self.cpu_time_limit = float(os.getenv("JUDGE0_CPU_LIMIT", "5"))
        self.memory_limit = int(os.getenv("JUDGE0_MEMORY_LIMIT", "262144"))  # 256 MB
        self._reachable = None  # Cached reachability result

    @property
    def available(self) -> bool:
        """Check if Judge0 API is actually reachable (cached)."""
        if self._reachable is not None:
            return self._reachable

        if not self.api_url:
            self._reachable = False
            return False

        try:
            resp = requests.get(
                f"{self.api_url}/about",
                headers=self._get_headers(),
                timeout=3,
            )
            self._reachable = resp.status_code == 200
            if self._reachable:
                print(f"✓ Judge0 is reachable at {self.api_url}")
            else:
                print(f"⚠ Judge0 returned status {resp.status_code}")
                self._reachable = False
        except Exception:
            print(f"⚠ Judge0 not reachable at {self.api_url}. Using local execution fallback.")
            self._reachable = False

        return self._reachable

    def _get_headers(self) -> Dict[str, str]:
        """Build request headers (include API key if RapidAPI)."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            # RapidAPI format
            headers["X-RapidAPI-Key"] = self.api_key
            headers["X-RapidAPI-Host"] = "judge0-ce.p.rapidapi.com"
        return headers

    def _get_language_id(self, language: str) -> Optional[int]:
        """Map language name to Judge0 language ID."""
        return LANGUAGE_MAP.get(language)

    # -----------------------------------------------------------------------
    # Core execution (Judge0 API)
    # -----------------------------------------------------------------------

    def run_test(self, code: str, lang_id: int, stdin: str) -> Dict:
        """
        Submit a single test case to Judge0.

        Args:
            code: Source code to execute.
            lang_id: Judge0 language ID.
            stdin: Standard input for the test case.

        Returns:
            Judge0 response dict (contains stdout, stderr, status, etc.)
        """
        payload = {
            "source_code": base64.b64encode(code.encode()).decode(),
            "language_id": lang_id,
            "stdin": base64.b64encode(stdin.encode()).decode(),
            "cpu_time_limit": self.cpu_time_limit,
            "memory_limit": self.memory_limit,
            "enable_network": False,
        }

        url = f"{self.api_url}/submissions?base64_encoded=true&wait=true"

        # Retry with exponential backoff for rate limits
        max_retries = 3
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    url,
                    json=payload,
                    headers=self._get_headers(),
                    timeout=self.timeout,
                )

                if resp.status_code == 429:
                    # Rate limited — back off
                    wait_time = 2 ** attempt
                    print(f"Judge0 rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                resp.raise_for_status()
                return resp.json()

            except requests.exceptions.Timeout:
                print(f"Judge0 timeout on attempt {attempt + 1}")
                continue
            except requests.exceptions.RequestException as e:
                print(f"Judge0 request failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return {"status": {"id": -1, "description": str(e)}}

        return {"status": {"id": -1, "description": "Max retries exceeded"}}

    def check_output(self, result: Dict, expected: str) -> bool:
        """
        Compare Judge0 output against expected output.

        Args:
            result: Judge0 submission result dict.
            expected: Expected output string.

        Returns:
            True if output matches expected (after stripping whitespace).
        """
        status_id = result.get("status", {}).get("id", -1)

        # Status 3 = "Accepted" (program ran successfully)
        if status_id != 3:
            return False

        raw_stdout = result.get("stdout") or ""
        try:
            actual = base64.b64decode(raw_stdout).decode().strip()
        except Exception:
            actual = raw_stdout.strip()

        return actual == expected.strip()

    # -----------------------------------------------------------------------
    # Local execution fallback (Python only)
    # -----------------------------------------------------------------------

    def _run_local_python(self, code: str, stdin: str, timeout: float = 5.0) -> Dict:
        """
        Run Python code locally in a sandboxed subprocess.

        Args:
            code: Python source code.
            stdin: Standard input string.
            timeout: Max execution time in seconds.

        Returns:
            Dict with status, stdout, stderr (same shape as Judge0 response).
        """
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, dir=tempfile.gettempdir()
        ) as f:
            f.write(code)
            tmp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, tmp_path],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=timeout,
                # Security: run with reduced privileges
                env={
                    "PATH": os.environ.get("PATH", ""),
                    "HOME": tempfile.gettempdir(),
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
            )

            if result.returncode == 0:
                return {
                    "status": {"id": 3, "description": "Accepted"},
                    "stdout": base64.b64encode(result.stdout.encode()).decode(),
                    "stderr": result.stderr or "",
                    "time": "0.0",
                    "memory": 0,
                }
            else:
                return {
                    "status": {"id": 11, "description": "Runtime Error"},
                    "stdout": base64.b64encode(result.stdout.encode()).decode() if result.stdout else "",
                    "stderr": result.stderr or "",
                }

        except subprocess.TimeoutExpired:
            return {
                "status": {"id": 5, "description": "Time Limit Exceeded"},
                "stdout": "",
                "stderr": "Execution timed out",
            }
        except Exception as e:
            return {
                "status": {"id": -1, "description": str(e)},
                "stdout": "",
                "stderr": str(e),
            }
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    # -----------------------------------------------------------------------
    # Local execution fallback (C++)
    # -----------------------------------------------------------------------

    def _run_local_cpp(self, code: str, stdin: str, timeout: float = 10.0) -> Dict:
        """
        Compile and run C++ code locally using g++.

        Args:
            code: C++ source code (with includes and main).
            stdin: Standard input string.
            timeout: Max execution time in seconds.

        Returns:
            Dict with status, stdout, stderr (same shape as Judge0 response).
        """
        tmp_dir = tempfile.mkdtemp(prefix="evaluator_cpp_")
        src_path = os.path.join(tmp_dir, "solution.cpp")
        bin_path = os.path.join(tmp_dir, "solution")

        try:
            with open(src_path, 'w') as f:
                f.write(code)

            # Compile with g++
            compile_result = subprocess.run(
                ["g++", "-std=c++17", "-O2", "-o", bin_path, src_path],
                capture_output=True, text=True, timeout=15,
            )

            if compile_result.returncode != 0:
                return {
                    "status": {"id": 6, "description": "Compilation Error"},
                    "stdout": "",
                    "stderr": compile_result.stderr[:500],
                }

            # Run the compiled binary
            run_result = subprocess.run(
                [bin_path],
                input=stdin, capture_output=True, text=True, timeout=timeout,
                env={"PATH": os.environ.get("PATH", ""), "HOME": tmp_dir},
            )

            if run_result.returncode == 0:
                return {
                    "status": {"id": 3, "description": "Accepted"},
                    "stdout": base64.b64encode(run_result.stdout.encode()).decode(),
                    "stderr": run_result.stderr or "",
                }
            else:
                return {
                    "status": {"id": 11, "description": "Runtime Error"},
                    "stdout": base64.b64encode(run_result.stdout.encode()).decode() if run_result.stdout else "",
                    "stderr": run_result.stderr or "",
                }

        except subprocess.TimeoutExpired:
            return {
                "status": {"id": 5, "description": "Time Limit Exceeded"},
                "stdout": "", "stderr": "Execution timed out",
            }
        except FileNotFoundError:
            return {
                "status": {"id": -1, "description": "g++ not found. Install Xcode CLI tools: xcode-select --install"},
                "stdout": "", "stderr": "g++ not found",
            }
        except Exception as e:
            return {
                "status": {"id": -1, "description": str(e)},
                "stdout": "", "stderr": str(e),
            }
        finally:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)

    # -----------------------------------------------------------------------
    # Auto-wrapping for class-based solutions (LeetCode style)
    # -----------------------------------------------------------------------

    @staticmethod
    def _wrap_class_solution(code: str, stdin: str) -> str:
        """
        Auto-wrap LeetCode-style 'class Solution:' code with a main block.

        Detects the first non-__init__ method and generates code that:
        1. Reads stdin
        2. Creates a Solution instance
        3. Calls the method with stdin as arguments
        4. Prints the result

        Args:
            code: Student's class-based code.
            stdin: The test case input string.

        Returns:
            Wrapped code ready for execution, or original code if no wrapping needed.
        """
        import re as _re
        import ast as _ast

        # Only wrap if there's a class Solution
        if 'class Solution' not in code:
            return code

        try:
            tree = _ast.parse(code)
        except SyntaxError:
            return code

        # Find the Solution class and its first non-__init__ method
        method_name = None
        param_count = 0
        for node in _ast.walk(tree):
            if isinstance(node, _ast.ClassDef) and node.name == 'Solution':
                for item in node.body:
                    if isinstance(item, _ast.FunctionDef) and item.name != '__init__':
                        method_name = item.name
                        # Exclude 'self' from param count
                        params = [a.arg for a in item.args.args if a.arg != 'self']
                        param_count = len(params)
                        break
                break

        if not method_name:
            return code

        # Generate wrapper code
        wrapper = f"""
import sys
import json

# Read stdin
_raw_input = sys.stdin.read().strip()

# Parse input - try different formats
def _parse_input(raw):
    '''Parse stdin into Python objects.'''
    # Try JSON first (e.g., [-1, 0, 1, 2, -1, -4])
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [parsed]
        return [parsed]
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Try space-separated numbers (e.g., "-1 0 1 2 -1 -4")
    parts = raw.split()
    try:
        nums = [int(x) for x in parts]
        return [nums]
    except ValueError:
        pass
    
    # Try comma-separated (e.g., "-1,0,1,2,-1,-4")  
    parts = raw.split(',')
    try:
        nums = [int(x.strip()) for x in parts]
        return [nums]
    except ValueError:
        pass
    
    # Try multi-line (each line is a separate argument)
    lines = raw.strip().split('\\n')
    args = []
    for line in lines:
        line = line.strip()
        try:
            args.append(json.loads(line))
        except (json.JSONDecodeError, ValueError):
            try:
                args.append(int(line))
            except ValueError:
                args.append(line)
    return args

_args = _parse_input(_raw_input)

# Call the method
sol = Solution()
_result = sol.{method_name}(*_args[:{param_count}])
print(_result)
"""
        return code + "\n" + wrapper

    @staticmethod
    def _wrap_standalone_function(code: str) -> str:
        """
        Auto-wrap standalone Python functions (not in a class) with a main block.

        Used for mixed evaluations where code is extracted from .txt files
        as bare function definitions (e.g., `def binary_search(arr, target):`).

        Detects the first function and generates code that:
        1. Reads stdin
        2. Parses the arguments
        3. Calls the function
        4. Prints the result
        """
        import ast as _ast

        try:
            tree = _ast.parse(code)
        except SyntaxError:
            return code

        # Find top-level function definitions (skip if there are classes)
        functions = []
        has_main = False
        for node in _ast.iter_child_nodes(tree):
            if isinstance(node, _ast.ClassDef):
                return code  # Has classes — use class wrapper instead
            if isinstance(node, _ast.FunctionDef):
                functions.append(node)
            # Check for existing main block
            if isinstance(node, _ast.If):
                try:
                    if (isinstance(node.test, _ast.Compare) and
                        hasattr(node.test.left, 'id') and
                        node.test.left.id == '__name__'):
                        has_main = True
                except (AttributeError, IndexError):
                    pass

        # Skip if there's already a main block or no functions found
        if has_main or not functions:
            return code

        # Use the first function
        func = functions[0]
        func_name = func.name
        params = [a.arg for a in func.args.args if a.arg != 'self']
        param_count = len(params)

        wrapper = f"""
import sys
import json

# Read stdin
_raw_input = sys.stdin.read().strip()

def _parse_input(raw):
    '''Parse stdin into Python objects — handles multi-line JSON args.'''
    lines = raw.strip().split('\\n')
    args = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            args.append(json.loads(line))
        except (json.JSONDecodeError, ValueError):
            try:
                args.append(int(line))
            except ValueError:
                try:
                    args.append(float(line))
                except ValueError:
                    args.append(line)
    return args

_args = _parse_input(_raw_input)
_result = {func_name}(*_args[:{param_count}])
print(_result)
"""
        return code + "\n" + wrapper


    @staticmethod
    def _wrap_cpp_class_solution(code: str) -> str:
        """
        Auto-wrap LeetCode-style C++ 'class Solution' code with includes and main().

        Detects the first public method (not constructors/destructors) and generates
        a main() that reads stdin (multi-line: first line = array, second line = scalar),
        creates a Solution instance, calls the method, and prints the result.
        """
        import re as _re

        if 'class Solution' not in code:
            return code

        # Extract the first public method signature
        # Pattern: return_type method_name(params) {
        method_match = _re.search(
            r'(?:vector<[^>]+>|int|bool|string|double|float|long\s+long|void)\s+'
            r'(\w+)\s*\(([^)]*)\)',
            code
        )
        if not method_match:
            return code

        method_name = method_match.group(1)
        params_str = method_match.group(2)

        # Skip constructors/destructors
        if method_name in ('Solution', '~Solution'):
            return code

        # Parse parameter types
        params = []
        for p in params_str.split(','):
            p = p.strip()
            if not p:
                continue
            params.append(p)

        # Determine return type
        ret_match = _re.search(
            r'((?:vector<[^>]+>|int|bool|string|double|float|long\s+long|void))\s+'
            + _re.escape(method_name),
            code
        )
        return_type = ret_match.group(1) if ret_match else 'auto'

        # Build stdin parsing + method call
        read_lines = []
        call_args = []
        arg_idx = 0

        for param in params:
            arg_name = f'arg{arg_idx}'
            if 'vector<int>' in param or 'vector<long' in param:
                read_lines.append(f'    // Parse {param}')
                read_lines.append(f'    string line{arg_idx};')
                read_lines.append(f'    getline(cin, line{arg_idx});')
                read_lines.append(f'    vector<int> {arg_name};')
                read_lines.append(f'    {{')
                read_lines.append(f'        stringstream ss(line{arg_idx});')
                read_lines.append(f'        char c; int val;')
                read_lines.append(f'        while(ss >> c) {{')
                read_lines.append(f'            if(c == \'[\' || c == \',\' || c == \']\') {{')
                read_lines.append(f'                if(ss >> val) {arg_name}.push_back(val);')
                read_lines.append(f'            }} else {{')
                read_lines.append(f'                ss.putback(c);')
                read_lines.append(f'                if(ss >> val) {arg_name}.push_back(val);')
                read_lines.append(f'            }}')
                read_lines.append(f'        }}')
                read_lines.append(f'    }}')
                call_args.append(arg_name)
            elif 'vector<string>' in param:
                read_lines.append(f'    string line{arg_idx};')
                read_lines.append(f'    getline(cin, line{arg_idx});')
                read_lines.append(f'    vector<string> {arg_name};')
                read_lines.append(f'    // simplified: treat as single string')
                read_lines.append(f'    {arg_name}.push_back(line{arg_idx});')
                call_args.append(arg_name)
            elif 'int' in param or 'long' in param:
                read_lines.append(f'    string line{arg_idx};')
                read_lines.append(f'    getline(cin, line{arg_idx});')
                read_lines.append(f'    int {arg_name} = stoi(line{arg_idx});')
                call_args.append(arg_name)
            elif 'string' in param:
                read_lines.append(f'    string {arg_name};')
                read_lines.append(f'    getline(cin, {arg_name});')
                call_args.append(arg_name)
            elif 'double' in param or 'float' in param:
                read_lines.append(f'    string line{arg_idx};')
                read_lines.append(f'    getline(cin, line{arg_idx});')
                read_lines.append(f'    double {arg_name} = stod(line{arg_idx});')
                call_args.append(arg_name)
            elif 'bool' in param:
                read_lines.append(f'    string line{arg_idx};')
                read_lines.append(f'    getline(cin, line{arg_idx});')
                read_lines.append(f'    bool {arg_name} = (line{arg_idx} == "true" || line{arg_idx} == "1");')
                call_args.append(arg_name)
            else:
                read_lines.append(f'    // Unknown param type: {param}')
                read_lines.append(f'    string {arg_name};')
                read_lines.append(f'    getline(cin, {arg_name});')
                call_args.append(arg_name)
            arg_idx += 1

        read_block = '\n'.join(read_lines)
        call_str = ', '.join(call_args)

        # Build print logic based on return type
        if 'vector' in return_type:
            print_block = '''    cout << "[";
    for(int i = 0; i < (int)result.size(); i++) {
        if(i > 0) cout << ",";
        cout << result[i];
    }
    cout << "]" << endl;'''
        elif return_type == 'bool':
            print_block = '    cout << (result ? "true" : "false") << endl;'
        elif return_type == 'string':
            print_block = '    cout << "\\"" << result << "\\"" << endl;'
        elif return_type == 'void':
            print_block = '    // void return type'
        else:
            print_block = '    cout << result << endl;'

        # Check what headers are already included
        needs_headers = []
        if '#include' not in code:
            needs_headers = [
                '#include <iostream>',
                '#include <vector>',
                '#include <string>',
                '#include <sstream>',
                '#include <unordered_map>',
                '#include <unordered_set>',
                '#include <algorithm>',
                '#include <map>',
                '#include <set>',
                '#include <climits>',
                'using namespace std;',
            ]
        else:
            # Add any missing essentials
            if '<sstream>' not in code:
                needs_headers.append('#include <sstream>')
            if 'using namespace std' not in code:
                needs_headers.append('using namespace std;')

        header_block = '\n'.join(needs_headers)

        wrapper = f"""
{header_block}

{code}

int main() {{
{read_block}
    Solution sol;
    {return_type} result = sol.{method_name}({call_str});
{print_block}
    return 0;
}}
"""
        return wrapper

    # -----------------------------------------------------------------------
    # Aggregate scoring
    # -----------------------------------------------------------------------

    def compute_test_score(
        self, code: str, language: str, test_cases: List[Dict]
    ) -> float:
        """
        Run all test cases and compute a pass rate (0–100).

        Uses Judge0 if available, otherwise falls back to local execution
        for Python. Returns 0 for unsupported languages when Judge0 is down.

        For LeetCode-style 'class Solution:' code, auto-wraps with a main
        block that reads stdin and calls the method.

        Args:
            code: Student source code.
            language: Language name ("python", "cpp", etc.)
            test_cases: List of {"stdin": str, "expected_output": str}.

        Returns:
            Score from 0 to 100.
        """
        if not test_cases:
            return 0

        use_judge0 = self.available
        use_local_python = (not use_judge0 and language == "python")
        use_local_cpp = (not use_judge0 and language == "cpp")
        use_local = use_local_python or use_local_cpp

        if use_judge0:
            lang_id = self._get_language_id(language)
            if lang_id is None:
                print(f"Judge0: unsupported language '{language}'")
                return 0
        elif not use_local:
            # Not Judge0, not Python/C++ — can't run tests
            print(f"⚠ Cannot run {language} tests: Judge0 unavailable and local execution only supports Python and C++.")
            return 0

        passed = 0
        details = []
        for i, tc in enumerate(test_cases):
            stdin = tc.get("stdin", "")
            expected = tc.get("expected_output", "")

            # Wrap class-based solutions for local execution
            exec_code = code
            if use_local_python and 'class Solution' in code:
                exec_code = self._wrap_class_solution(code, stdin)
            elif use_local_python and 'class Solution' not in code and 'def ' in code:
                # Standalone Python functions (e.g., extracted from .txt files)
                exec_code = self._wrap_standalone_function(code)
            elif (use_local_cpp or use_judge0) and language == 'cpp' and 'class Solution' in code:
                exec_code = self._wrap_cpp_class_solution(code)

            if use_judge0:
                result = self.run_test(exec_code, lang_id, stdin)
            elif use_local_cpp:
                result = self._run_local_cpp(exec_code, stdin)
            else:
                result = self._run_local_python(exec_code, stdin)

            is_pass = self.check_output(result, expected)
            if is_pass:
                passed += 1

            status_desc = result.get("status", {}).get("description", "Unknown")
            # Show actual output for debugging
            actual_out = ""
            try:
                raw = result.get("stdout", "")
                if raw:
                    import base64 as _b64
                    actual_out = _b64.b64decode(raw).decode().strip()[:80]
            except Exception:
                pass
            details.append(
                f"  TC{i+1}: {'✓ PASS' if is_pass else '✗ FAIL'} ({status_desc})"
                + (f" got='{actual_out}'" if not is_pass and actual_out else "")
            )

        score = round((passed / len(test_cases)) * 100)
        mode = "Judge0" if use_judge0 else "local"
        print(f"Test execution ({mode}): {passed}/{len(test_cases)} passed = {score}%")
        for d in details:
            print(d)

        return score
