import re
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class ZPLCommand:
    name: str
    params: List[str]
    raw: str

class ZPLParser:
    """
    Parses a ZPL string into a list of ZPLCommand objects.
    """
    def __init__(self):
        # Pattern to match ^ or ~ followed by 1-3 uppercase letters, 
        # then everything until the next ^ or ~
        self.cmd_pattern = re.compile(r'([\^~][A-Z0-9]{1,3})([^~^]*)')

    def parse(self, zpl_data: str) -> List[ZPLCommand]:
        commands = []
        # Don't strip all whitespace, only outer. ^FD needs its internal spaces!
        zpl_data = zpl_data.strip().replace('\n', '').replace('\r', '')
        
        matches = self.cmd_pattern.findall(zpl_data)
        for cmd_raw_name, cmd_content in matches:
            prefix = cmd_raw_name[0]
            
            # Whitelist common 2-letter (3-char total) commands
            # Added DF and XF here
            if cmd_raw_name[:3] in ['^XA', '^XZ', '^FO', '^FD', '^FS', '^GB', '^GC', '^FR', '^BC', '^BQ', '^GF', '^LH', '^LL', '^CF', '^FW', '^DF', '^XF', '^FN']:
                name = cmd_raw_name[:3]
                extra = cmd_raw_name[3:]
            else:
                name = prefix + cmd_raw_name[1] # e.g. ^A
                extra = cmd_raw_name[2:]
            
            params = []
            full_params_string = extra + cmd_content
            
            if name == '^A' and full_params_string and not full_params_string.startswith(','):
                # Handle ^A0R logic
                font = full_params_string[0]
                remaining = full_params_string[1:]
                params.append(font)
                if remaining and remaining[0] in 'NRIBNRIB':
                    params.append(remaining[0])
                    params.extend(remaining[1:].lstrip(',').split(',') if len(remaining) > 1 else [])
                else:
                    params.extend(remaining.lstrip(',').split(',') if remaining else [])
            else:
                if full_params_string:
                    params = full_params_string.split(',')
            
            commands.append(ZPLCommand(name=name, params=params, raw=f"{cmd_raw_name}{cmd_content}"))
            
        return commands
