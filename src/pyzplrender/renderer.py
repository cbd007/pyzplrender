from PIL import Image, ImageDraw, ImageFont
from .parser import ZPLParser, ZPLCommand
from typing import List, Dict
import os

class ZPLRenderer:
    """
    Renders ZPL commands onto a Pillow image canvas.
    """
    def __init__(self, width_mm: float, height_mm: float, dpmm: int = 8):
        self.dpmm = dpmm
        self.width_dots = int(width_mm * dpmm)
        self.height_dots = int(height_mm * dpmm)
        self.image = Image.new('1', (self.width_dots, self.height_dots), color=1)
        self.draw = ImageDraw.Draw(self.image)
        
        # Printer State
        self.current_x = 0
        self.current_y = 0
        self.label_home_x = 0
        self.label_home_y = 0
        self.reverse_field = False
        self.default_orientation = 'N'
        self.current_orientation = 'N'
        
        # Font State
        self.default_font_name = '0'
        self.default_font_height = 30
        self.default_font_width = 30
        self.active_font_name = '0'
        self.active_font_height = 30
        self.active_font_width = 30
        self.active_font = ImageFont.load_default()
        self._update_active_font()

        # Field Block State
        self.block_width = 0
        self.block_max_lines = 1
        self.block_line_spacing = 0
        self.block_justification = 'L'

        # Phase 6: Macro & Template State
        self.formats: Dict[str, List[ZPLCommand]] = {}
        self.variables: Dict[str, str] = {}
        self.is_downloading = False
        self.download_format_name = ""
        self.download_buffer: List[ZPLCommand] = []
        
        self.parser = ZPLParser()
        self.current_cmd_idx = 0
        self._parsed_commands: List[ZPLCommand] = []

    def _update_active_font(self):
        font_paths = ["/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:\\Windows\\Fonts\\arial.ttf"]
        for p in font_paths:
            if os.path.exists(p):
                try:
                    self.active_font = ImageFont.truetype(p, self.active_font_height)
                    return
                except: continue
        self.active_font = ImageFont.load_default()

    def render(self, zpl_data: str):
        commands = self.parser.parse(zpl_data)
        # If this block contains an ^XF (recall), we should collect variables from the WHOLE block first
        has_recall = any(c.name == '^XF' for c in commands)
        if has_recall:
            self._collect_variables(commands)
            
        self._parsed_commands = commands
        for i, cmd in enumerate(commands):
            self.current_cmd_idx = i
            self._execute_command(cmd)

    def _collect_variables(self, commands: List[ZPLCommand]):
        for i, cmd in enumerate(commands):
            if cmd.name == '^FN' and len(cmd.params) > 0:
                var_num = cmd.params[0]
                for j in range(i + 1, len(commands)):
                    if commands[j].name == '^FD':
                        self.variables[var_num] = ",".join(commands[j].params)
                        break
                    if commands[j].name in ['^XA', '^XZ']: break

    def _execute_command(self, cmd: ZPLCommand):
        name, params = cmd.name, cmd.params
        if self.is_downloading and name != '^XZ':
            self.download_buffer.append(cmd)
            return

        if name == '^XA': self.current_orientation = self.default_orientation
        elif name == '^XZ':
            if self.is_downloading:
                self.formats[self.download_format_name] = self.download_buffer
                self.is_downloading, self.download_buffer = False, []
        elif name == '^DF':
            if params: self.download_format_name, self.is_downloading, self.download_buffer = params[0], True, []
        elif name == '^XF':
            if params and params[0] in self.formats:
                stored = self.formats[params[0]]
                orig_cmds, orig_idx = self._parsed_commands, self.current_cmd_idx
                self._parsed_commands = stored
                # We are executing the STORED commands.
                # These might contain ^FN which will trigger drawing using collected variables.
                for i, c in enumerate(stored):
                    self.current_cmd_idx = i
                    self._execute_command(c)
                self._parsed_commands, self.current_cmd_idx = orig_cmds, orig_idx
        elif name == '^LH':
            if len(params) > 0 and params[0]: self.label_home_x = int(params[0])
            if len(params) > 1 and params[1]: self.label_home_y = int(params[1])
        elif name == '^FB':
            if len(params) > 0 and params[0]: self.block_width = int(params[0])
            if len(params) > 1 and params[1]: self.block_max_lines = int(params[1])
            if len(params) > 3 and params[3]: self.block_justification = params[3]
        elif name == '^CF':
            if len(params) > 0 and params[0]: self.default_font_name = params[0]
            if len(params) > 1 and params[1]: self.default_font_height = int(params[1])
            if len(params) > 2 and params[2]: self.default_font_width = int(params[2])
            self.active_font_name, self.active_font_height, self.active_font_width = self.default_font_name, self.default_font_height, self.default_font_width
            self._update_active_font()
        elif name == '^FW':
            if params: self.default_orientation = self.current_orientation = params[0]
        elif name == '^FO':
            if len(params) > 0 and params[0]: self.current_x = self.label_home_x + int(params[0])
            if len(params) > 1 and params[1]: self.current_y = self.label_home_y + int(params[1])
            self.current_orientation, self.block_width, self.block_max_lines, self.block_justification = self.default_orientation, 0, 1, 'L'
        elif name == '^FR': self.reverse_field = True
        elif name == '^A':
            if len(params) > 0 and params[0]: self.active_font_name = params[0]
            if len(params) > 1 and params[1]: self.current_orientation = params[1]
            if len(params) > 2 and params[2]: self.active_font_height = int(params[2])
            if len(params) > 3 and params[3]: self.active_font_width = int(params[3])
            self._update_active_font()
        elif name == '^GB':
            w, h, t = int(params[0]) if len(params)>0 and params[0] else 1, int(params[1]) if len(params)>1 and params[1] else 1, int(params[2]) if len(params)>2 and params[2] else 1
            rounding = int(params[4]) if len(params) > 4 and params[4] else 0
            color = 1 if self.reverse_field else 0
            if rounding > 0: self._draw_rounded_rectangle([self.current_x, self.current_y, self.current_x+w, self.current_y+h], rounding, color, t)
            else: self.draw.rectangle([self.current_x, self.current_y, self.current_x+w, self.current_y+h], outline=color, width=t)
            self.reverse_field = False
        elif name == '^GC':
            d, t = int(params[0]) if len(params)>0 and params[0] else 1, int(params[1]) if len(params)>1 and params[1] else 1
            color = 1 if self.reverse_field else 0
            self.draw.ellipse([self.current_x, self.current_y, self.current_x+d, self.current_y+d], outline=color, width=t)
            self.reverse_field = False
        elif name in ['^BC', '^BQ']:
            if params: self.current_orientation = params[0]
        elif name == '^GF':
            try:
                bpr = int(params[3]) if len(params) > 3 and params[3] else 0
                hex_data = params[4] if len(params) > 4 else ""
                if hex_data and bpr: self._render_graphic_field(hex_data, bpr)
            except: pass
        elif name == '^FD':
            # Skip drawing ^FD if we are in a Recall block but NOT inside the template itself
            # In ZPL, ^FN1^FDValue is just an assignment.
            # We detect this by checking if ^FN was just executed AND we aren't in a template
            is_template_cmd = any(f == self._parsed_commands for f in self.formats.values())
            
            if self.current_cmd_idx > 0:
                prev = self._parsed_commands[self.current_cmd_idx - 1]
                if prev.name == '^FN' and not is_template_cmd:
                    # This is just an assignment, skip the draw!
                    return

            text = ",".join(params)
            # Variable substitution if we ARE in a template
            if self.current_cmd_idx > 0:
                prev = self._parsed_commands[self.current_cmd_idx - 1]
                if prev.name == '^FN' and prev.params and prev.params[0] in self.variables:
                    text = self.variables[prev.params[0]]
            
            last = self._get_last_meaningful_cmd()
            if last == '^BC': self._render_barcode_128(text)
            elif last == '^BQ': self._render_qrcode(text)
            else: self._render_text(text)
            self.reverse_field = False
        elif name == '^FN': pass
        elif name == '^FS': self.reverse_field = False

    def _get_last_meaningful_cmd(self) -> str:
        for i in range(self.current_cmd_idx - 1, -1, -1):
            c = self._parsed_commands[i]
            if c.name == '^FN': continue
            if c.name in ['^BC', '^BQ', '^FO', '^XA']: return c.name
        return ""

    def _draw_rounded_rectangle(self, xy, radius, outline, width):
        x1, y1, x2, y2 = xy
        r = (radius / 8.0) * (min(x2-x1, y2-y1) // 2)
        self.draw.arc([x1, y1, x1 + 2*r, y1 + 2*r], 180, 270, fill=outline, width=width)
        self.draw.arc([x2 - 2*r, y1, x2, y1 + 2*r], 270, 0, fill=outline, width=width)
        self.draw.arc([x2 - 2*r, y2 - 2*r, x2, y2], 0, 90, fill=outline, width=width)
        self.draw.arc([x1, y2 - 2*r, x1 + 2*r, y2], 90, 180, fill=outline, width=width)
        self.draw.line([x1 + r, y1, x2 - r, y1], fill=outline, width=width)
        self.draw.line([x1 + r, y2, x2 - r, y2], fill=outline, width=width)
        self.draw.line([x1, y1 + r, x1, y2 - r], fill=outline, width=width)
        self.draw.line([x2, y1 + r, x2, y2 - r], fill=outline, width=width)

    def _render_text(self, text: str):
        color = 1 if self.reverse_field else 0
        if self.block_width > 0:
            lines = self._wrap_text(text, self.block_width)[:self.block_max_lines]
            y = self.current_y
            for line in lines:
                x = self.current_x
                bbox = self.draw.textbbox((0, 0), line, font=self.active_font)
                w = bbox[2] - bbox[0]
                if self.block_justification == 'C': x += (self.block_width - w) // 2
                elif self.block_justification == 'R': x += (self.block_width - w)
                self._draw_maybe_rotated_text(line, x, y, color)
                y += self.active_font_height
        else: self._draw_maybe_rotated_text(text, self.current_x, self.current_y, color)

    def _wrap_text(self, text: str, width: int) -> List[str]:
        words, lines, cur = text.split(' '), [], []
        for w in words:
            test = ' '.join(cur + [w])
            bbox = self.draw.textbbox((0, 0), test, font=self.active_font)
            if bbox[2] - bbox[0] <= width: cur.append(w)
            else:
                if cur: lines.append(' '.join(cur))
                cur = [w]
        if cur: lines.append(' '.join(cur))
        return lines

    def _draw_maybe_rotated_text(self, text: str, x: int, y: int, color: int):
        if self.current_orientation == 'N' or not self.current_orientation:
            self.draw.text((x, y), text, font=self.active_font, fill=color)
        else:
            bbox = self.draw.textbbox((0, 0), text, font=self.active_font)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            txt_img = Image.new('1', (w + 4, h + 4), color=1)
            ImageDraw.Draw(txt_img).text((2, 2), text, font=self.active_font, fill=0)
            rotated = txt_img.rotate(self._get_rotation_angle(self.current_orientation), expand=True, fillcolor=1)
            if self.reverse_field: rotated = rotated.point(lambda x: 0 if x else 1)
            self.image.paste(rotated, (x, y))

    def _get_rotation_angle(self, code: str) -> int: return {'N': 0, 'R': 270, 'I': 180, 'B': 90}.get(code, 0)

    def _render_barcode_128(self, data: str):
        try:
            import barcode
            from barcode.writer import ImageWriter
            bc = barcode.get_barcode_class('code128')(data.lstrip(">:").lstrip(">;"), writer=ImageWriter())
            bc_img = bc.render({"module_width": 0.3, "module_height": 10.0, "font_size": 0, "text_distance": 0}).convert('1')
            if self.current_orientation != 'N': bc_img = bc_img.rotate(self._get_rotation_angle(self.current_orientation), expand=True, fillcolor=1)
            self.image.paste(bc_img, (self.current_x, self.current_y))
        except: self.draw.text((self.current_x, self.current_y), f"[BC128:{data}]", fill=0)

    def _render_qrcode(self, data: str):
        try:
            import qrcode
            qr = qrcode.QRCode(box_size=4, border=0)
            qr.add_data(data.split(',', 1)[-1] if ',' in data else data)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white").convert('1')
            if self.current_orientation != 'N': qr_img = qr_img.rotate(self._get_rotation_angle(self.current_orientation), expand=True, fillcolor=1)
            self.image.paste(qr_img, (self.current_x, self.current_y))
        except: self.draw.text((self.current_x, self.current_y), f"[QR:{data}]", fill=0)

    def _render_graphic_field(self, hex_data: str, bytes_per_row: int):
        try:
            hex_data = "".join(hex_data.split()).replace('~', '')
            raw_bytes = bytes.fromhex(hex_data)
            img = Image.frombytes('1', (bytes_per_row * 8, len(raw_bytes) // bytes_per_row), raw_bytes, 'raw', '1', 0, 1).point(lambda x: 0 if x else 1)
            self.image.paste(img, (self.current_x, self.current_y))
        except Exception as e: print(f"Error rendering GF: {e}")

    def save_png(self, output_path: str):
        self.image.save(output_path, format="PNG")
