from mock import patch
class helper:
  def __init__(self):
    self.xxx = 3
class real:
  def __init__(self):
    self.dict = helper()


class real2:
  def __init__(self):
    self.dict = {}


r = real()
with patch.object( r.dict, 'xxx', new = [123] ) as mock_future:
  assert r.dict.xxx == [123]

def MockHelper():
  h = helper()
  h.xxx = [123]
  return h

r2 = real2()
with patch.dict( r2.dict, { 1: MockHelper() } ):
  assert r2.dict[ 1 ].xxx == [123]
