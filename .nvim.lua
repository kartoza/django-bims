-- SPDX-FileCopyrightText: Kartoza
-- SPDX-License-Identifier: AGPL-3.0
--
-- Neovim project-specific configuration for Django BIMS
-- This file is automatically loaded by neovim when opening the project
--
-- Made with love by Kartoza | https://kartoza.com

-- Ensure we're in the project directory
local project_root = vim.fn.getcwd()

-- Set Python path for LSP and debugging
vim.env.PYTHONPATH = project_root
vim.env.DJANGO_SETTINGS_MODULE = "core.settings.dev"

-- Configure Python interpreter (use venv if available)
local venv_python = project_root .. "/.venv/bin/python"
if vim.fn.filereadable(venv_python) == 1 then
  vim.g.python3_host_prog = venv_python
end

-- Database environment for Django
vim.env.DATABASE_NAME = "bims"
vim.env.DATABASE_USERNAME = vim.env.USER
vim.env.DATABASE_PASSWORD = ""
vim.env.DATABASE_HOST = project_root .. "/.pgdata"
vim.env.DATABASE_PORT = "5432"

-- DAP (Debug Adapter Protocol) configuration for Python/Django
local dap_ok, dap = pcall(require, "dap")
if dap_ok then
  dap.adapters.python = {
    type = "executable",
    command = venv_python,
    args = { "-m", "debugpy.adapter" },
  }

  dap.configurations.python = {
    {
      type = "python",
      request = "launch",
      name = "Django: runserver",
      program = project_root .. "/manage.py",
      args = { "runserver", "0.0.0.0:8000", "--noreload" },
      django = true,
      justMyCode = false,
      env = {
        DJANGO_SETTINGS_MODULE = "core.settings.dev",
      },
    },
    {
      type = "python",
      request = "launch",
      name = "Django: test",
      program = project_root .. "/manage.py",
      args = { "test", "bims" },
      django = true,
      justMyCode = false,
      env = {
        DJANGO_SETTINGS_MODULE = "core.settings.test",
      },
    },
    {
      type = "python",
      request = "attach",
      name = "Attach to debugpy (5678)",
      connect = {
        host = "127.0.0.1",
        port = 5678,
      },
      pathMappings = {
        {
          localRoot = project_root,
          remoteRoot = project_root,
        },
      },
    },
    {
      type = "python",
      request = "launch",
      name = "Python: Current File",
      program = "${file}",
      pythonPath = venv_python,
    },
  }
end

-- Which-key configuration for project-specific keybindings
local wk_ok, wk = pcall(require, "which-key")
if wk_ok then
  wk.add({
    { "<leader>p", group = "BIMS Project" },

    -- Development Server
    { "<leader>ps", group = "Server" },
    {
      "<leader>pss",
      function()
        vim.cmd("terminal bims-runserver")
      end,
      desc = "Start Django runserver",
    },
    {
      "<leader>psd",
      function()
        vim.cmd("terminal bims-debug")
      end,
      desc = "Start with debugpy",
    },
    {
      "<leader>psn",
      function()
        vim.cmd("terminal bims-nginx-start")
      end,
      desc = "Start Nginx",
    },
    {
      "<leader>psN",
      function()
        vim.cmd("terminal bims-nginx-stop")
      end,
      desc = "Stop Nginx",
    },

    -- Database
    { "<leader>pd", group = "Database" },
    {
      "<leader>pds",
      function()
        vim.cmd("terminal bims-pg-start")
      end,
      desc = "Start PostgreSQL",
    },
    {
      "<leader>pdS",
      function()
        vim.cmd("terminal bims-pg-stop")
      end,
      desc = "Stop PostgreSQL",
    },
    {
      "<leader>pdt",
      function()
        vim.cmd("terminal bims-pg-status")
      end,
      desc = "PostgreSQL status",
    },
    {
      "<leader>pdp",
      function()
        vim.cmd("terminal bims-psql")
      end,
      desc = "Open psql shell",
    },
    {
      "<leader>pdm",
      function()
        vim.cmd("terminal bims-migrate")
      end,
      desc = "Run migrations",
    },
    {
      "<leader>pdM",
      function()
        vim.cmd("terminal bims-makemigrations")
      end,
      desc = "Make migrations",
    },

    -- Testing
    { "<leader>pt", group = "Testing" },
    {
      "<leader>pta",
      function()
        vim.cmd("terminal bims-test")
      end,
      desc = "Run all tests",
    },
    {
      "<leader>ptf",
      function()
        local file = vim.fn.expand("%:p")
        vim.cmd("terminal bims-test " .. file)
      end,
      desc = "Test current file",
    },
    {
      "<leader>ptc",
      function()
        vim.cmd("terminal pytest --cov=bims --cov-report=html")
      end,
      desc = "Run with coverage",
    },

    -- Celery
    { "<leader>pc", group = "Celery" },
    {
      "<leader>pcw",
      function()
        vim.cmd("terminal bims-celery-worker")
      end,
      desc = "Start Celery worker",
    },
    {
      "<leader>pcb",
      function()
        vim.cmd("terminal bims-celery-beat")
      end,
      desc = "Start Celery beat",
    },

    -- Code Quality
    { "<leader>pq", group = "Quality" },
    {
      "<leader>pql",
      function()
        vim.cmd("terminal bims-lint")
      end,
      desc = "Run linters",
    },
    {
      "<leader>pqf",
      function()
        vim.cmd("terminal bims-format")
      end,
      desc = "Format code",
    },
    {
      "<leader>pqs",
      function()
        vim.cmd("terminal bims-security-check")
      end,
      desc = "Security scan",
    },
    {
      "<leader>pqp",
      function()
        vim.cmd("terminal bims-precommit-run")
      end,
      desc = "Pre-commit checks",
    },
    {
      "<leader>pqr",
      function()
        vim.cmd("terminal bims-reuse-check")
      end,
      desc = "REUSE compliance",
    },
    {
      "<leader>pqF",
      function()
        -- Format current file with black and isort
        local file = vim.fn.expand("%:p")
        vim.cmd("!black " .. file .. " && isort " .. file)
        vim.cmd("e!")
      end,
      desc = "Format current file",
    },

    -- Django Management
    { "<leader>pm", group = "Manage" },
    {
      "<leader>pms",
      function()
        vim.cmd("terminal bims-shell")
      end,
      desc = "Django shell",
    },
    {
      "<leader>pmc",
      function()
        vim.cmd("terminal bims-collectstatic")
      end,
      desc = "Collect static",
    },
    {
      "<leader>pmu",
      function()
        vim.cmd("terminal bims-createsuperuser")
      end,
      desc = "Create superuser",
    },
    {
      "<leader>pmr",
      function()
        vim.cmd("terminal python manage.py rebuildindex")
      end,
      desc = "Rebuild search index",
    },

    -- Environment
    { "<leader>pe", group = "Environment" },
    {
      "<leader>pes",
      function()
        vim.cmd("terminal bims-dev-start")
      end,
      desc = "Start dev environment",
    },
    {
      "<leader>peS",
      function()
        vim.cmd("terminal bims-dev-stop")
      end,
      desc = "Stop dev environment",
    },
    {
      "<leader>pei",
      function()
        vim.cmd("terminal bims-pip-install")
      end,
      desc = "Install pip fallback packages",
    },
    {
      "<leader>pen",
      function()
        vim.cmd("terminal bims-npm-install")
      end,
      desc = "Install npm packages",
    },
    {
      "<leader>pep",
      function()
        vim.cmd("terminal bims-precommit-install")
      end,
      desc = "Install pre-commit hooks",
    },
    {
      "<leader>peP",
      function()
        vim.cmd("terminal bims-package-status")
      end,
      desc = "Show package status",
    },

    -- Frontend/Webpack
    { "<leader>pf", group = "Frontend" },
    {
      "<leader>pfb",
      function()
        vim.cmd("terminal bims-webpack-build")
      end,
      desc = "Build frontend",
    },
    {
      "<leader>pfw",
      function()
        vim.cmd("terminal bims-webpack-watch")
      end,
      desc = "Watch frontend",
    },

    -- Git
    { "<leader>pg", group = "Git" },
    {
      "<leader>pgs",
      function()
        vim.cmd("terminal git status")
      end,
      desc = "Git status",
    },
    {
      "<leader>pgd",
      function()
        vim.cmd("terminal git diff")
      end,
      desc = "Git diff",
    },
    {
      "<leader>pgD",
      function()
        vim.cmd("terminal git diff --staged")
      end,
      desc = "Git diff staged",
    },
    {
      "<leader>pgl",
      function()
        vim.cmd("terminal git log --oneline -20")
      end,
      desc = "Git log",
    },
    {
      "<leader>pgL",
      function()
        vim.cmd("terminal git log --graph --oneline --all -30")
      end,
      desc = "Git log graph",
    },
    {
      "<leader>pgc",
      function()
        vim.ui.input({ prompt = "Commit message: " }, function(msg)
          if msg then
            vim.cmd("terminal git add -A && git commit -m '" .. msg .. "'")
          end
        end)
      end,
      desc = "Git commit (all)",
    },
    {
      "<leader>pgC",
      function()
        vim.cmd("terminal git add -p")
      end,
      desc = "Git add interactive",
    },
    {
      "<leader>pgp",
      function()
        vim.cmd("terminal git push")
      end,
      desc = "Git push",
    },
    {
      "<leader>pgP",
      function()
        vim.cmd("terminal git pull --rebase")
      end,
      desc = "Git pull (rebase)",
    },
    {
      "<leader>pgb",
      function()
        vim.cmd("terminal git branch -a")
      end,
      desc = "Git branches",
    },
    {
      "<leader>pgB",
      function()
        vim.ui.input({ prompt = "New branch name: " }, function(name)
          if name then
            vim.cmd("terminal git checkout -b " .. name)
          end
        end)
      end,
      desc = "Git new branch",
    },
    {
      "<leader>pgS",
      function()
        vim.cmd("terminal git stash")
      end,
      desc = "Git stash",
    },
    {
      "<leader>pgR",
      function()
        vim.cmd("terminal git stash pop")
      end,
      desc = "Git stash pop",
    },

    -- GitHub (complements Octo plugin - use :Octo for full GitHub integration)
    { "<leader>pG", group = "GitHub/CI" },
    {
      "<leader>pGo",
      function()
        vim.cmd("Octo")
      end,
      desc = "Open Octo",
    },
    {
      "<leader>pGa",
      function()
        vim.cmd("terminal gh run list")
      end,
      desc = "List CI runs",
    },
    {
      "<leader>pGw",
      function()
        vim.cmd("terminal gh run watch")
      end,
      desc = "Watch CI run",
    },
    {
      "<leader>pGc",
      function()
        vim.cmd("terminal gh pr checks")
      end,
      desc = "PR checks status",
    },
    {
      "<leader>pGr",
      function()
        vim.cmd("terminal gh repo view --web")
      end,
      desc = "Open repo in browser",
    },
    {
      "<leader>pGs",
      function()
        vim.cmd("terminal gh api repos/:owner/:repo/actions/runs --jq '.workflow_runs[:5] | .[] | \"\\(.status) \\(.conclusion // \"running\") - \\(.name)\"'")
      end,
      desc = "CI status summary",
    },

    -- Debug
    { "<leader>pD", group = "Debug" },
    {
      "<leader>pDd",
      function()
        require("dap").continue()
      end,
      desc = "Start/Continue",
    },
    {
      "<leader>pDq",
      function()
        require("dap").terminate()
      end,
      desc = "Stop/Quit",
    },
    {
      "<leader>pDb",
      function()
        require("dap").toggle_breakpoint()
      end,
      desc = "Toggle breakpoint",
    },
    {
      "<leader>pDB",
      function()
        vim.ui.input({ prompt = "Breakpoint condition: " }, function(cond)
          if cond then
            require("dap").set_breakpoint(cond)
          end
        end)
      end,
      desc = "Conditional breakpoint",
    },
    {
      "<leader>pDl",
      function()
        vim.ui.input({ prompt = "Log message: " }, function(msg)
          if msg then
            require("dap").set_breakpoint(nil, nil, msg)
          end
        end)
      end,
      desc = "Log point",
    },
    {
      "<leader>pDo",
      function()
        require("dap").step_over()
      end,
      desc = "Step over",
    },
    {
      "<leader>pDi",
      function()
        require("dap").step_into()
      end,
      desc = "Step into",
    },
    {
      "<leader>pDO",
      function()
        require("dap").step_out()
      end,
      desc = "Step out",
    },
    {
      "<leader>pDc",
      function()
        require("dap").run_to_cursor()
      end,
      desc = "Run to cursor",
    },
    {
      "<leader>pDr",
      function()
        require("dap").repl.open()
      end,
      desc = "Open REPL",
    },
    {
      "<leader>pDu",
      function()
        local ok, dapui = pcall(require, "dapui")
        if ok then
          dapui.toggle()
        else
          vim.notify("dap-ui not installed", vim.log.levels.WARN)
        end
      end,
      desc = "Toggle DAP UI",
    },
    {
      "<leader>pDe",
      function()
        local ok, dapui = pcall(require, "dapui")
        if ok then
          dapui.eval()
        else
          -- Fallback to basic eval
          vim.ui.input({ prompt = "Expression: " }, function(expr)
            if expr then
              require("dap").repl.execute(expr)
            end
          end)
        end
      end,
      desc = "Evaluate expression",
    },
    {
      "<leader>pDh",
      function()
        require("dap.ui.widgets").hover()
      end,
      desc = "Hover variable",
    },
    {
      "<leader>pDs",
      function()
        local widgets = require("dap.ui.widgets")
        widgets.centered_float(widgets.scopes)
      end,
      desc = "Show scopes",
    },
    {
      "<leader>pDf",
      function()
        local widgets = require("dap.ui.widgets")
        widgets.centered_float(widgets.frames)
      end,
      desc = "Show frames",
    },
    {
      "<leader>pDL",
      function()
        require("dap").list_breakpoints()
      end,
      desc = "List breakpoints",
    },
    {
      "<leader>pDC",
      function()
        require("dap").clear_breakpoints()
      end,
      desc = "Clear all breakpoints",
    },
    {
      "<leader>pDR",
      function()
        require("dap").restart()
      end,
      desc = "Restart session",
    },
  })
end

-- Treesitter ensure installed for this project
local ts_ok, ts = pcall(require, "nvim-treesitter.configs")
if ts_ok then
  ts.setup({
    ensure_installed = {
      "python",
      "html",
      "htmldjango",
      "css",
      "javascript",
      "json",
      "yaml",
      "toml",
      "bash",
      "sql",
      "lua",
      "nix",
      "markdown",
      "markdown_inline",
    },
  })
end

-- LSP settings for this project
vim.api.nvim_create_autocmd("LspAttach", {
  callback = function(args)
    local client = vim.lsp.get_client_by_id(args.data.client_id)
    if client and client.name == "pyright" then
      client.config.settings = client.config.settings or {}
      client.config.settings.python = client.config.settings.python or {}
      client.config.settings.python.analysis = client.config.settings.python.analysis or {}
      client.config.settings.python.analysis.extraPaths = { project_root }
    end
  end,
})

-- Auto-format Python files on save (if you want this behavior)
-- vim.api.nvim_create_autocmd("BufWritePre", {
--   pattern = "*.py",
--   callback = function()
--     vim.lsp.buf.format({ async = false })
--   end,
-- })

-- Custom commands for this project
vim.api.nvim_create_user_command("BimsRunserver", "terminal bims-runserver", {})
vim.api.nvim_create_user_command("BimsMigrate", "terminal bims-migrate", {})
vim.api.nvim_create_user_command("BimsTest", "terminal bims-test", {})
vim.api.nvim_create_user_command("BimsShell", "terminal bims-shell", {})
vim.api.nvim_create_user_command("BimsDebug", "terminal bims-debug", {})
vim.api.nvim_create_user_command("BimsLint", "terminal bims-lint", {})
vim.api.nvim_create_user_command("BimsFormat", "terminal bims-format", {})

-- Notify user that project config is loaded
vim.notify("Django BIMS project config loaded. Use <leader>p for project menu.", vim.log.levels.INFO)
