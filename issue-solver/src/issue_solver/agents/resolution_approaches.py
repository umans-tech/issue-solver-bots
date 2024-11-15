def resolution_approach_prompt(location: str, pr_description: str) -> str:
    return f"""
        <uploaded_files>
        {location}
        </uploaded_files>
        I've uploaded a python code repository in the directory {location} (not in /tmp/inputs). Consider the following PR description:
        
        <pr_description>
        {pr_description}
        </pr_description>
        
        Can you help me implement the necessary changes to the repository so that the requirements specified in the <pr_description> are met?
        I've already taken care of all changes to any of the test files described in the <pr_description>. This means you DON'T have to modify the testing logic or any of the tests in any way!
        
        Your task is to make the minimal changes to non-tests files in the {location} directory to ensure the <pr_description> is satisfied.
        
        Follow these steps to resolve the issue:
        1. As a first step, it might be a good idea to explore the repo to familiarize yourself with its structure.
        2. Create a script to reproduce the error and execute it with `python <filename.py>` using the BashTool, to confirm the error
        3. Edit the sourcecode of the repo to resolve the issue
        4. Rerun your reproduce script and confirm that the error is fixed!
        5. Think about edgecases and make sure your fix handles them as well
        
        Your thinking should be thorough and so it's fine if it's very long.
    """
