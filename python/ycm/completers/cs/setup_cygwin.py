import json
import codecs
import re

with codecs.open("Omnisharp/bin/Debug/config.json", "r+", encoding = "utf-8") as jsonfile:
  jsontext = jsonfile.read()
  if jsontext.startswith(u'\ufeff'):
    jsontext = jsontext[1:]

  jsontext = re.sub(r"\/\*.*\*\/", "", jsontext, flags = re.DOTALL)

  data = json.loads(jsontext, 'utf-8')

  if not data.has_key("UseCygpath"):
    data["UseCygpath"] = True

    jsonfile.seek(0)
    jsonfile.write(json.dumps(data))
    jsonfile.truncate()
