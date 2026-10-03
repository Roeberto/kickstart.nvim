vim.pack.add { 'https://github.com/rmagatti/auto-session' }

-- Sesja zapisuje się i wczytuje automatycznie dla katalogu, w którym uruchomiono nvim
vim.o.sessionoptions = 'blank,buffers,curdir,folds,help,tabpages,winsize,winpos,terminal,localoptions'

require('auto-session').setup {
  suppressed_dirs = { '~/', '~/Downloads', '/' },
}
