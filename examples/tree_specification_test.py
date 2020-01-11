import ast




def perfectEval(anonstring):
    try:
        ev = ast.literal_eval(anonstring)
        return ev
    except ValueError:
        corrected = "\'" + anonstring + "\'"
        ev = ast.literal_eval(corrected)
        return ev


def treespec_parse(line):
    cmt_idx = line.find("#")
    if cmt_idx==-1:
        cmt_idx = None
    ll = line[:cmt_idx]
    if "=" in ll:
        parts = ll.split("=")
        key = parts[0].strip()
        litstr = parts[1].strip()
        #import pdb; pdb.set_trace()
        try:
            value = ast.literal_eval(litstr)
        except ValueError:
            litstr = f"\"{litstr}\""
            value = ast.literal_eval(litstr)
        except SyntaxError:
            print(f"Warning could not parse {line}")
            return None
    else:
        return None
    return key, value


if __name__ == "__main__":
    line = "one=1"
    k,v = treespec_parse(line)
    print(f"k={k}, v={v}")
