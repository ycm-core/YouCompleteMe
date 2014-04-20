import vim
class Dispatch:
  def __new__(tp, **kw):
    try:
      if vim.eval('has("gui_running")') != '0':
        return GTK(**kw)
      elif 'tty_patch' in kw and kw['tty_patch']:
        return TTY(**kw)
    except:
      pass
    return Nop(**kw)

class Nop:
  def __init__(self, **kw):
    return
  def Cleanup(self):
    return
  def __call__(self):
    return

try:
  import termios
  import fcntl
  class TTY(Nop):
    def __init__(self, **kw):
      vim.command('nnoremap \uFEFF <CursorHold>')
      vim.command('onoremap \uFEFF <CursorHold>')
      vim.command('vnoremap \uFEFF <CursorHold>')
      vim.command('inoremap \uFEFF <CursorHold>')
      vim.command('cnoremap \uFEFF <Nop>')

    def __call__(self):
      for i in '\ufeff'.encode('utf-8'):
        fcntl.ioctl(0, termios.TIOCSTI, bytes([i]))
except:
  pass


try:
  from gi.repository import GLib
  import os
  class GTK:
    def __init__(self, **kw):
      self.pipe=os.pipe()
      ch=GLib.IOChannel(self.pipe[0])
      ch.set_flags(GLib.IOFlags.NONBLOCK)
      self.source=GLib.io_add_watch(ch, GLib.IOCondition.IN, self.Callback)

    def Callback(self, ch, flags):
      ch.read_to_end()
      ch.read(1)
      vim.command('doautocmd CursorHold')
      return True

    def Cleanup(self):
      from gi.repository import GLib
      GLib.source_remove(self.source)
      os.close(self.pipe[0])
      os.close(self.pipe[1])
      self.pipe=None

    def __call__(self):
      if self.pipe:
        os.write(self.pipe[1], b'!')
except:
  pass

# vim: expandtab:ts=2:sw=2:sts=2
