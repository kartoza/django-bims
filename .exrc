" SPDX-FileCopyrightText: Kartoza
" SPDX-License-Identifier: AGPL-3.0
"
" Vim/Neovim project-specific configuration for Django BIMS
" This file is automatically loaded by vim when opening the project
"
" Made with love by Kartoza | https://kartoza.com

" Set Python path for this project
let $PYTHONPATH = getcwd()
let $DJANGO_SETTINGS_MODULE = 'core.settings.dev'

" Database environment
let $DATABASE_NAME = 'bims'
let $DATABASE_USERNAME = $USER
let $DATABASE_PASSWORD = ''
let $DATABASE_HOST = getcwd() . '/.pgdata'
let $DATABASE_PORT = '5432'

" Use project virtualenv
if filereadable('.venv/bin/python')
  let g:python3_host_prog = getcwd() . '/.venv/bin/python'
endif

" File type settings
autocmd FileType python setlocal tabstop=4 shiftwidth=4 softtabstop=4 expandtab
autocmd FileType html,htmldjango setlocal tabstop=2 shiftwidth=2 softtabstop=2 expandtab
autocmd FileType javascript,json,yaml setlocal tabstop=2 shiftwidth=2 softtabstop=2 expandtab
autocmd FileType css,scss setlocal tabstop=2 shiftwidth=2 softtabstop=2 expandtab

" Ignore patterns for this project
set wildignore+=*.pyc,__pycache__,*.egg-info
set wildignore+=.venv/*,venv/*,node_modules/*
set wildignore+=static/*,media/*,logs/*
set wildignore+=.git/*,.pgdata/*

" Project-specific commands
command! BimsRunserver terminal bims-runserver
command! BimsMigrate terminal bims-migrate
command! BimsMakemigrations terminal bims-makemigrations
command! BimsTest terminal bims-test
command! BimsShell terminal bims-shell
command! BimsDebug terminal bims-debug
command! BimsLint terminal bims-lint
command! BimsFormat terminal bims-format
command! BimsPgStart terminal bims-pg-start
command! BimsPgStop terminal bims-pg-stop
command! BimsNginxStart terminal bims-nginx-start
command! BimsNginxStop terminal bims-nginx-stop
command! BimsCeleryWorker terminal bims-celery-worker
command! BimsDevStart terminal bims-dev-start
command! BimsDevStop terminal bims-dev-stop
command! BimsPrecommit terminal bims-precommit-run
command! BimsSecurityCheck terminal bims-security-check

" Which-key mappings (if which-key is available, .nvim.lua has better support)
" These are fallback mappings for vanilla vim/neovim without which-key

" Leader + p prefix for project commands
nnoremap <leader>pss :BimsRunserver<CR>
nnoremap <leader>psd :BimsDebug<CR>
nnoremap <leader>psn :BimsNginxStart<CR>
nnoremap <leader>psN :BimsNginxStop<CR>

nnoremap <leader>pds :BimsPgStart<CR>
nnoremap <leader>pdS :BimsPgStop<CR>
nnoremap <leader>pdm :BimsMigrate<CR>
nnoremap <leader>pdM :BimsMakemigrations<CR>
nnoremap <leader>pdp :terminal bims-psql<CR>

nnoremap <leader>pta :BimsTest<CR>
nnoremap <leader>ptf :execute 'terminal bims-test ' . expand('%:p')<CR>

nnoremap <leader>pcw :BimsCeleryWorker<CR>

nnoremap <leader>pql :BimsLint<CR>
nnoremap <leader>pqf :BimsFormat<CR>
nnoremap <leader>pqs :BimsSecurityCheck<CR>
nnoremap <leader>pqp :BimsPrecommit<CR>

nnoremap <leader>pms :BimsShell<CR>
nnoremap <leader>pmc :terminal bims-collectstatic<CR>

nnoremap <leader>pes :BimsDevStart<CR>
nnoremap <leader>peS :BimsDevStop<CR>

" Git mappings
nnoremap <leader>pgs :terminal git status<CR>
nnoremap <leader>pgd :terminal git diff<CR>
nnoremap <leader>pgD :terminal git diff --staged<CR>
nnoremap <leader>pgl :terminal git log --oneline -20<CR>
nnoremap <leader>pgp :terminal git push<CR>
nnoremap <leader>pgP :terminal git pull --rebase<CR>
nnoremap <leader>pgb :terminal git branch -a<CR>

" GitHub/CI (use :Octo for full GitHub integration)
nnoremap <leader>pGo :Octo<CR>
nnoremap <leader>pGa :terminal gh run list<CR>
nnoremap <leader>pGw :terminal gh run watch<CR>
nnoremap <leader>pGc :terminal gh pr checks<CR>

" Quick access mappings
nnoremap <leader>pr :BimsRunserver<CR>
nnoremap <leader>pt :BimsTest<CR>
nnoremap <leader>pl :BimsLint<CR>
nnoremap <leader>pf :BimsFormat<CR>

" Print help for project commands
function! BimsHelp()
  echo "Django BIMS Project Commands"
  echo "============================"
  echo ""
  echo "Server:"
  echo "  <leader>pss  - Start Django runserver"
  echo "  <leader>psd  - Start with debugpy"
  echo "  <leader>psn  - Start Nginx"
  echo "  <leader>psN  - Stop Nginx"
  echo ""
  echo "Database:"
  echo "  <leader>pds  - Start PostgreSQL"
  echo "  <leader>pdS  - Stop PostgreSQL"
  echo "  <leader>pdm  - Run migrations"
  echo "  <leader>pdM  - Make migrations"
  echo "  <leader>pdp  - Open psql"
  echo ""
  echo "Testing:"
  echo "  <leader>pta  - Run all tests"
  echo "  <leader>ptf  - Test current file"
  echo ""
  echo "Celery:"
  echo "  <leader>pcw  - Start Celery worker"
  echo ""
  echo "Quality:"
  echo "  <leader>pql  - Run linters"
  echo "  <leader>pqf  - Format code"
  echo "  <leader>pqs  - Security scan"
  echo "  <leader>pqp  - Pre-commit checks"
  echo ""
  echo "Management:"
  echo "  <leader>pms  - Django shell"
  echo "  <leader>pmc  - Collect static"
  echo ""
  echo "Environment:"
  echo "  <leader>pes  - Start dev environment"
  echo "  <leader>peS  - Stop dev environment"
  echo ""
  echo "Git:"
  echo "  <leader>pgs  - Git status"
  echo "  <leader>pgd  - Git diff"
  echo "  <leader>pgD  - Git diff staged"
  echo "  <leader>pgl  - Git log"
  echo "  <leader>pgp  - Git push"
  echo "  <leader>pgP  - Git pull (rebase)"
  echo "  <leader>pgb  - Git branches"
  echo ""
  echo "GitHub/CI (use :Octo for PRs/issues):"
  echo "  <leader>pGo  - Open Octo"
  echo "  <leader>pGa  - List CI runs"
  echo "  <leader>pGw  - Watch CI run"
  echo "  <leader>pGc  - PR checks"
  echo ""
  echo "Debug (.nvim.lua has full DAP support):"
  echo "  <leader>pDd  - Start/Continue"
  echo "  <leader>pDb  - Toggle breakpoint"
  echo "  <leader>pDo  - Step over"
  echo "  <leader>pDi  - Step into"
  echo "  <leader>pDO  - Step out"
  echo ""
  echo "Quick Access:"
  echo "  <leader>pr   - Runserver"
  echo "  <leader>pt   - Test"
  echo "  <leader>pl   - Lint"
  echo "  <leader>pf   - Format"
endfunction
command! BimsHelp call BimsHelp()
nnoremap <leader>ph :BimsHelp<CR>

" Notify that project config is loaded
echom "Django BIMS project config loaded. Use :BimsHelp or <leader>ph for commands."
