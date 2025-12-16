"""Interactive TUI Status view for MemoFlow (k9s-style)"""

import logging
import subprocess
import shutil
from pathlib import Path
from typing import Optional, List
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import DataTable, Header, Footer, Input, Static, Label
from rich.text import Text
from textual.binding import Binding
from textual.message import Message
from textual import events
from mf.core.file_manager import FileManager
from mf.core.hash_manager import HashManager
from mf.core.schema_manager import SchemaManager
from mf.core.git_engine import GitEngine
from mf.models.memo import Memo

logger = logging.getLogger(__name__)


class StatusTUI(App):
    """Interactive Status TUI Application"""
    
    TITLE = "mf status"
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    Vertical {
        height: 1fr;
    }
    
    #table-container {
        height: 1fr;
    }
    
    #filter-input {
        height: 3;
        border: solid $accent;
    }
    
    #detail-panel {
        height: 1fr;
        border: solid $success;
        padding: 1;
        display: none;
    }
    
    DataTable {
        border: solid $primary;
    }
    
    .filter-active {
        border: solid $warning;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True, show=False),
        Binding("/", "toggle_filter", "Filter", priority=True, show=False),
        Binding("enter", "view_detail", "View", priority=False, show=False),
        Binding("escape", "close_detail_or_editor", "Close", priority=True, show=False),
        Binding("r", "refresh", "Refresh", priority=True, show=False),
        Binding("t", "toggle_type", "Type", priority=True),
        Binding("s", "toggle_status", "Status", priority=True),
        Binding("e", "open_editor", "Editor", priority=True),
        Binding("c", "change_type", "Change Type", priority=True),
        Binding("u", "change_status", "Change Status", priority=True),
        Binding("n", "capture", "New/Capture", priority=True),
        Binding("m", "move_file", "Move", priority=True),
        Binding("R", "rebuild_index", "Rebuild Index", priority=True),
        Binding("l", "show_list", "List View", priority=True),
        Binding("T", "show_timeline", "Timeline", priority=True),
        Binding("C", "show_calendar", "Calendar", priority=True),
        Binding("S", "show_schema", "Schema", priority=True),
        Binding("A", "select_area", "Area", priority=True),
        Binding("G", "select_category", "Category", priority=True),
    ]
    
    def __init__(self, repo_root: Path, editor: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.repo_root = repo_root
        self.all_files: List[Memo] = []
        self.filtered_files: List[Memo] = []
        self.current_filter: Optional[str] = None
        self.type_filter: Optional[str] = None
        self.status_filter: Optional[str] = None
        self.current_area_id: Optional[int] = None
        self.current_category_range: Optional[tuple[float, float]] = None
        self.current_view: str = "Items"
        self.selected_row: Optional[int] = None
        self._pending_action: Optional[tuple] = None  # 用于存储待处理的操作
        self._editor_process: Optional[subprocess.Popen] = None  # 用于存储编辑器进程（GUI编辑器）
        self._editor_mode: bool = False  # 标记是否在编辑器模式
        
        # 配置编辑器
        self.editor = editor or self._detect_editor()
        
        # 初始化服务
        self.hash_mgr = HashManager(repo_root)
        self.schema_mgr = SchemaManager(repo_root)
        self.git_engine = GitEngine(repo_root)
        self.file_mgr = FileManager(repo_root, self.hash_mgr, self.schema_mgr, self.git_engine)
    
    def _detect_editor(self) -> str:
        """自动检测可用的编辑器，优先使用 vim"""
        # 按优先级检测编辑器，vim 优先
        editors = [
            ("vim", ["vim"]),
            ("vi", ["vi"]),
            ("typora", ["typora"]),
            ("vscode", ["code", "code-insiders"]),
            ("notepad++", ["notepad++"]),
            ("nano", ["nano"]),
        ]
        
        for editor_name, commands in editors:
            for cmd in commands:
                if shutil.which(cmd):
                    logger.info(f"Detected editor: {editor_name} ({cmd})")
                    return cmd
        
        # 如果都没找到，尝试使用系统默认编辑器
        import os
        if os.name == 'nt':  # Windows
            return "notepad"
        else:  # Unix-like
            return os.environ.get("EDITOR", "vim")
    
    def compose(self) -> ComposeResult:
        """创建应用布局"""
        yield Header(show_clock=True)
        with Vertical():
            yield Static("", id="context-bar")
            yield Static("", id="stats")
            with Horizontal():
                yield DataTable(id="file-table")
                yield Static(id="detail-panel")
            yield Input(placeholder="Filter (type, status, or search)...", id="filter-input", classes="hidden")
        yield Footer()
    
    def on_mount(self) -> None:
        """应用挂载时初始化"""
        table = self.query_one("#file-table", DataTable)
        table.add_columns("#", "Hash", "ID", "Title", "Type", "Status")
        table.cursor_type = "row"
        
        self.refresh_data()
        self.update_table()
        self.update_stats()
        self.update_context_bar()
        
        # 设置焦点到表格
        table.focus()
    
    def on_key(self, event: events.Key) -> None:
        """处理按键事件，确保 c、u、n、m 等按键能正常工作"""
        # 如果编辑器模式激活，只有 ESC 键有效
        if self._editor_mode:
            if event.key == "escape":
                self.action_close_editor()
                event.prevent_default()
                event.stop()
            return
        
        # ESC 键处理：优先关闭详情面板，然后是编辑器
        if event.key == "escape":
            self.action_close_detail_or_editor()
            event.prevent_default()
            event.stop()
            return
        
        # 检查输入框是否有焦点，如果有焦点且有 pending_action，阻止 Enter 键的 action binding
        try:
            filter_input = self.query_one("#filter-input", Input)
            if not filter_input.has_class("hidden") and filter_input.has_focus:
                # 如果输入框有焦点且有 pending_action，Enter 键应该提交输入，而不是触发 action_view_detail
                if event.key == "enter" and self._pending_action:
                    # 阻止 action binding，让输入框的 on_input_submitted 处理
                    event.prevent_default()
                    event.stop()
                    # 手动触发 Input.Submitted 事件
                    filter_input.post_message(Input.Submitted(filter_input, filter_input.value))
                    return
                # 如果输入框有焦点但没有 pending_action，Enter 键也应该被输入框处理（用于正常过滤）
                elif event.key == "enter":
                    # 让输入框自己处理 Enter 键（可能会触发 Input.Submitted）
                    return
        except Exception as e:
            logger.debug(f"Error in on_key check: {e}")
        
        # 如果按键是 c、u、n、m、R、l、T、C、A、G，直接调用对应的 action
        # 这样可以确保即使 DataTable 捕获了按键，也能正常工作
        if event.key == "c":
            self.action_change_type()
            event.prevent_default()
            event.stop()
        elif event.key == "u":
            self.action_change_status()
            event.prevent_default()
            event.stop()
        elif event.key == "n":
            self.action_capture()
            event.prevent_default()
            event.stop()
        elif event.key == "m":
            self.action_move_file()
            event.prevent_default()
            event.stop()
        elif event.key == "R":
            self.action_rebuild_index()
            event.prevent_default()
            event.stop()
        elif event.key == "l":
            self.action_show_list()
            event.prevent_default()
            event.stop()
        elif event.key == "T":
            self.action_show_timeline()
            event.prevent_default()
            event.stop()
        elif event.key == "C":
            self.action_show_calendar()
            event.prevent_default()
            event.stop()
        elif event.key in ("a", "A"):
            self.action_select_area()
            event.prevent_default()
            event.stop()
        elif event.key in ("g", "G"):
            self.action_select_category()
            event.prevent_default()
            event.stop()
    
    def refresh_data(self) -> None:
        """刷新数据"""
        self.all_files = self.file_mgr.query()
        self.apply_filters()
    
    def apply_filters(self) -> None:
        """应用所有过滤器"""
        self.filtered_files = self.all_files.copy()
        
        # Area/Category 过滤（基于 JD ID）
        if self.current_area_id is not None or self.current_category_range is not None:
            filtered_by_location: List[Memo] = []
            for memo in self.filtered_files:
                try:
                    # 解析 ID: PREFIX-AREA.ITEMPART
                    _, numeric = memo.id.split("-", 1)
                    area_str, item_str = numeric.split(".", 1)
                    area_id = int(area_str)
                    # item_id 作为 float，形如 11.001 或 11.01
                    item_val = float(f"{area_str}.{item_str}")
                except Exception:
                    # ID 格式异常时直接跳过（不纳入过滤结果）
                    continue
                
                if self.current_area_id is not None and area_id != self.current_area_id:
                    continue
                
                if self.current_category_range is not None:
                    start, end = self.current_category_range
                    if not (start <= item_val <= end):
                        continue
                
                filtered_by_location.append(memo)
            
            self.filtered_files = filtered_by_location
        
        # 类型过滤
        if self.type_filter:
            self.filtered_files = [
                f for f in self.filtered_files 
                if (f.type or "untyped") == self.type_filter
            ]
        
        # 状态过滤
        if self.status_filter:
            self.filtered_files = [
                f for f in self.filtered_files 
                if f.status == self.status_filter
            ]
        
        # 文本搜索过滤
        if self.current_filter:
            filter_lower = self.current_filter.lower()
            self.filtered_files = [
                f for f in self.filtered_files
                if (filter_lower in f.title.lower() or
                    filter_lower in f.uuid.lower() or
                    filter_lower in f.id.lower() or
                    filter_lower in (f.type or "untyped").lower())
            ]
        
        # 按创建时间倒序排序
        self.filtered_files.sort(key=lambda x: x.created_at, reverse=True)
        
        # 更新上下文条
        self.update_context_bar()
    
    def update_stats(self) -> None:
        """更新统计信息（显示在表格上方）"""
        try:
            stats_widget = self.query_one("#stats", Static)
        except Exception as e:
            logger.warning(f"Stats widget not ready: {e}")
            return
        
        # 计算统计（支持动态前缀和两位/三位小数格式）
        schema = self.schema_mgr.get_schema()
        prefix = schema.user_prefix
        inbox_count = sum(1 for f in self.all_files 
                         if (not f.type or f.type == "") and (
                             f.id.startswith(f"{prefix}-00.") or 
                             f.id.startswith(f"{prefix}-00.0") or
                             f.id.startswith(f"{prefix}-00.00")
                         ))
        
        type_counts = {}
        for memo in self.all_files:
            if memo.status == "open":
                file_type = memo.type if memo.type else "untyped"
                type_counts[file_type] = type_counts.get(file_type, 0) + 1
        
        # 构建单行统计文本
        stats_parts = []
        
        if inbox_count > 0:
            stats_parts.append(f"Inbox: {inbox_count}")
        
        for file_type in ["task", "meeting", "note", "email"]:
            count = type_counts.get(file_type, 0)
            if count > 0:
                label = file_type.capitalize() + ("s" if count > 1 else "")
                stats_parts.append(f"{label}: {count}")
        
        stats_parts.append(f"Total: {len(self.all_files)}")
        
        if self.current_filter or self.type_filter or self.status_filter:
            stats_parts.append(f"Filtered: {len(self.filtered_files)}/{len(self.all_files)}")
        
        # 使用分隔符连接所有统计项
        if stats_parts:
            stats_text = " | ".join(stats_parts)
            # 将统计信息作为表格的第一行显示（使用特殊标记）
            stats_widget.update(stats_text)
        else:
            stats_widget.update("No files")

    def update_context_bar(self) -> None:
        """更新顶部资源上下文条（Namespace / Area / Category / View）"""
        try:
            ctx_widget = self.query_one("#context-bar", Static)
        except Exception as e:
            logger.debug(f"Context bar widget not ready: {e}")
            return

        # Namespace 名称：优先使用注册表中的名称，否则使用目录名
        repo_name = self.repo_root.name
        try:
            from mf.core.repo_registry import RepoRegistry

            registry = RepoRegistry()
            registered = registry.find_by_path(self.repo_root)
            if registered:
                repo_name = registered.name
        except Exception as e:
            logger.debug(f"Failed to resolve repo name from registry: {e}")

        # Area 显示
        area_display = "All"
        if self.current_area_id is not None:
            try:
                schema = self.schema_mgr.get_schema()
                area = schema.get_area(self.current_area_id)
                if area:
                    area_display = f"{self.current_area_id} ({area.name})"
                else:
                    area_display = str(self.current_area_id)
            except Exception:
                area_display = str(self.current_area_id)

        # Category 显示（基于 range）
        category_display = "All"
        if self.current_category_range is not None:
            start, end = self.current_category_range
            category_display = f"{start:.3f}-{end:.3f}"

        view_display = self.current_view

        ctx_text = (
            f"NS: {repo_name} | "
            f"Area: {area_display} | "
            f"Category: {category_display} | "
            f"View: {view_display}"
        )
        ctx_widget.update(ctx_text)
    
    def update_table(self) -> None:
        """更新表格数据"""
        table = self.query_one("#file-table", DataTable)
        table.clear()
        
        # 更新统计信息
        self.update_stats()
        
        for idx, memo in enumerate(self.filtered_files, start=1):
            display_type = memo.type if memo.type else "untyped"
            status_style = "green" if memo.status == "done" else "yellow"
            
            table.add_row(
                str(idx),
                memo.uuid,
                memo.id,
                memo.title[:40] + "..." if len(memo.title) > 40 else memo.title,
                display_type,
                f"[{status_style}]{memo.status}[/{status_style}]",
                key=str(memo.uuid)
            )
    
    def action_toggle_filter(self) -> None:
        """切换过滤器显示"""
        # 如果详情面板显示，按 / 键应该关闭详情面板（而不是切换过滤器）
        detail_panel = self.query_one("#detail-panel", Static)
        if detail_panel.display:
            self.action_close_detail()
            return
        
        # 如果编辑器模式激活，按 / 键应该退出编辑器模式
        if self._editor_mode:
            self.action_close_editor()
            return
        
        filter_input = self.query_one("#filter-input", Input)
        if filter_input.has_class("hidden"):
            # 如果有待处理的操作，先清除
            if self._pending_action:
                self._pending_action = None
            filter_input.placeholder = "Filter (type, status, or search)..."
            filter_input.remove_class("hidden")
            filter_input.focus()
        else:
            filter_input.add_class("hidden")
            filter_input.value = ""
            self.current_filter = None
            self._pending_action = None
            self.apply_filters()
            self.update_table()
            self.update_stats()
            self.query_one("#file-table", DataTable).focus()
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """过滤器输入变化"""
        if event.input.id == "filter-input":
            # 检查是否有待处理的操作
            if self._pending_action:
                return  # 等待用户按 Enter 确认
            
            self.current_filter = event.value
            self.apply_filters()
            self.update_table()
            self.update_stats()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """输入提交（按 Enter）"""
        logger.debug(f"Input submitted: {event.input.id}, value: {event.value}, pending_action: {self._pending_action}")
        
        if event.input.id == "filter-input":
            if self._pending_action:
                logger.debug(f"Pending action found: {self._pending_action}")
                action_type, memo = self._pending_action
                new_value = event.value.strip()
                
                if memo:
                    logger.debug(f"Processing pending action: {action_type}, memo: {memo.uuid}, new_value: {new_value}")
                else:
                    logger.debug(f"Processing pending action: {action_type}, new_value: {new_value}")
                
                # 先清除 pending_action，避免重复处理
                self._pending_action = None
                
                # 隐藏输入框
                event.input.add_class("hidden")
                event.input.value = ""
                event.input.placeholder = "Filter (type, status, or search)..."
                
                # 恢复焦点到表格
                self.query_one("#file-table", DataTable).focus()
                
                if action_type == "change_type":
                    # 验证类型
                    valid_types = ["task", "meeting", "note", "email"]
                    if new_value not in valid_types:
                        self.notify(f"Invalid type: {new_value}. Must be one of: {', '.join(valid_types)}", severity="error")
                        return
                    
                    try:
                        logger.debug(f"Updating type for {memo.uuid} to {new_value}")
                        self.file_mgr.update_file(
                            memo.uuid,
                            frontmatter_updates={"type": new_value},
                            commit_message=f"change type to {new_value}"
                        )
                        logger.debug(f"Successfully updated type for {memo.uuid} to {new_value}")
                        self.notify(f"✓ Type changed to {new_value}", severity="success", timeout=3.0)
                        # 刷新数据
                        self.refresh_data()
                        self.update_table()
                        self.update_stats()
                        logger.debug("Data refreshed after type change")
                    except Exception as e:
                        logger.error(f"Error changing type: {e}", exc_info=True)
                        self.notify(f"✗ Error: {e}", severity="error", timeout=5.0)
                
                elif action_type == "capture":
                    # 处理捕获操作
                    # 格式: "type:content" 或 "content"
                    input_value = new_value
                    file_type = None
                    content = ""
                    
                    # 检查是否有类型前缀（格式：type:content）
                    if ":" in input_value:
                        parts = input_value.split(":", 1)
                        if len(parts) == 2:
                            type_part = parts[0].strip()
                            content = parts[1].strip()
                            
                            valid_types = ["task", "meeting", "note", "email"]
                            if type_part in valid_types:
                                file_type = type_part
                            else:
                                self.notify(f"Invalid type: {type_part}. Must be one of: {', '.join(valid_types)}", severity="error")
                                return
                        else:
                            # 如果分割后不是两部分，说明格式不对，使用整个输入作为内容
                            content = input_value.strip()
                    else:
                        # 没有冒号，整个输入作为内容（untyped）
                        content = input_value.strip()
                    
                    if not content:
                        self.notify("Content cannot be empty", severity="error")
                        return
                    
                    try:
                        from mf.commands.capture import handle_capture
                        logger.debug(f"Capturing: type={file_type}, content={content[:50]}...")
                        hash_id, file_path = handle_capture(file_type, content, self.repo_root)
                        type_display = file_type if file_type else "untyped"
                        self.notify(f"✓ Captured ({type_display}): {file_path.name} (hash: {hash_id})", severity="success", timeout=3.0)
                        # 刷新数据
                        self.refresh_data()
                        self.update_table()
                        self.update_stats()
                        logger.debug("Data refreshed after capture")
                    except Exception as e:
                        logger.error(f"Error capturing: {e}", exc_info=True)
                        self.notify(f"✗ Error: {e}", severity="error", timeout=5.0)
                
                elif action_type == "move":
                    # 处理移动操作
                    # 支持两种格式：
                    # 1. area_id.category_id (如 "11.1" 表示区域11，类别1) - 自动生成下一个可用ID
                    # 2. 完整的 JD ID (如 "AC-11.001")
                    if not new_value:
                        self.notify("ID cannot be empty", severity="error")
                        return
                    
                    try:
                        new_jd_id = None
                        
                        # 检查是否是 area.category 格式（如 "11.1"）
                        if "." in new_value and not "-" in new_value:
                            # 尝试解析为 area_id.category_id 格式
                            try:
                                parts = new_value.split(".")
                                if len(parts) == 2:
                                    area_id = int(parts[0])
                                    category_id = int(parts[1])
                                    
                                    # 生成下一个可用的 ID
                                    new_jd_id = self.schema_mgr.generate_next_id(area_id, category_id, self.repo_root)
                                    if not new_jd_id:
                                        self.notify(f"No available ID in area {area_id}, category {category_id}", severity="error")
                                        return
                                    self.notify(f"Auto-generated ID: {new_jd_id}", severity="info", timeout=2.0)
                            except (ValueError, IndexError):
                                # 解析失败，当作完整的 JD ID 处理
                                new_jd_id = new_value.strip()
                        else:
                            # 完整的 JD ID 格式
                            new_jd_id = new_value.strip()
                        
                        if not new_jd_id:
                            self.notify("Invalid format. Use 'area.category' (e.g., 11.1) or JD ID (e.g., AC-11.001)", severity="error")
                            return
                        
                        logger.debug(f"Moving file {memo.uuid} from {memo.id} to {new_jd_id}")
                        from mf.commands.organize import handle_move
                        new_file_path = handle_move(memo.uuid, memo.id, new_jd_id, self.repo_root)
                        logger.debug(f"Successfully moved file {memo.uuid} to new ID {new_jd_id}")
                        self.notify(f"✓ Moved to: {new_file_path}", severity="success", timeout=3.0)
                        # 刷新数据
                        self.refresh_data()
                        self.update_table()
                        logger.debug("Data refreshed after move")
                    except Exception as e:
                        logger.error(f"Error moving file: {e}", exc_info=True)
                        self.notify(f"✗ Error: {e}", severity="error", timeout=5.0)
                
                elif action_type == "select_area":
                    # 选择 Area 过滤
                    new_area_id: Optional[int] = None
                    if new_value:
                        try:
                            new_area_id = int(new_value)
                        except ValueError:
                            self.notify(f"Invalid area id: {new_value}", severity="error")
                            return
                        # 验证 area 是否存在
                        try:
                            schema = self.schema_mgr.get_schema()
                            if not schema.get_area(new_area_id):
                                self.notify(f"Area {new_area_id} not found in schema", severity="error")
                                return
                        except Exception as e:
                            logger.error(f"Error validating area id: {e}", exc_info=True)
                            self.notify(f"Error validating area: {e}", severity="error")
                            return
                    
                    # 更新过滤状态：切换 area 会清除 category 过滤
                    self.current_area_id = new_area_id
                    self.current_category_range = None
                    
                    # 刷新视图
                    self.apply_filters()
                    self.update_table()
                    
                    if new_area_id is None:
                        self.notify("Area filter cleared (All areas)", severity="info", timeout=2.0)
                    else:
                        self.notify(f"Area filter set to {new_area_id}", severity="info", timeout=2.0)
                
                elif action_type == "select_category":
                    # 选择 Category 过滤（依赖当前 Area）
                    if self.current_area_id is None:
                        self.notify("Please select an Area first", severity="warning", timeout=3.0)
                        return
                    
                    new_category_range: Optional[tuple[float, float]] = None
                    if new_value:
                        try:
                            cat_id = int(new_value)
                        except ValueError:
                            self.notify(f"Invalid category id: {new_value}", severity="error")
                            return
                        
                        try:
                            schema = self.schema_mgr.get_schema()
                            area = schema.get_area(self.current_area_id)
                            if not area:
                                self.notify(f"Area {self.current_area_id} not found in schema", severity="error")
                                return
                            category = area.get_category(cat_id)
                            if not category:
                                self.notify(
                                    f"Category {cat_id} not found in area {self.current_area_id}",
                                    severity="error",
                                )
                                return
                            new_category_range = category.range
                        except Exception as e:
                            logger.error(f"Error validating category id: {e}", exc_info=True)
                            self.notify(f"Error validating category: {e}", severity="error")
                            return
                    
                    self.current_category_range = new_category_range
                    
                    # 刷新视图
                    self.apply_filters()
                    self.update_table()
                    
                    if new_category_range is None:
                        self.notify("Category filter cleared (All categories)", severity="info", timeout=2.0)
                    else:
                        start, end = new_category_range
                        self.notify(
                            f"Category filter set to range {start:.3f}-{end:.3f}",
                            severity="info",
                            timeout=2.0,
                        )
            else:
                # 没有 pending_action，这是正常的过滤器输入
                self.current_filter = event.value
                self.apply_filters()
                self.update_table()
                self.update_stats()
    
    def action_view_detail(self) -> None:
        """查看选中文件的详情"""
        # 如果输入框可见且有焦点，不处理 Enter 键（让输入框处理）
        try:
            filter_input = self.query_one("#filter-input", Input)
            if not filter_input.has_class("hidden") and filter_input.has_focus:
                # 如果有 pending_action，Enter 键应该提交输入，而不是查看详情
                if self._pending_action:
                    # 手动触发 Input.Submitted 事件，确保输入被处理
                    filter_input.post_message(Input.Submitted(filter_input, filter_input.value))
                    return  # 让输入框的 on_input_submitted 处理
        except:
            pass
        
        table = self.query_one("#file-table", DataTable)
        cursor_row = table.cursor_row
        
        if cursor_row is not None and cursor_row < len(self.filtered_files):
            memo = self.filtered_files[cursor_row]
            detail_panel = self.query_one("#detail-panel", Static)
            
            # 读取文件内容
            file_path = memo.file_path
            if not file_path or not file_path.exists():
                # 尝试从 hash_index 获取路径
                hash_index = self.hash_mgr.get_index()
                if memo.uuid in hash_index:
                    file_path = self.repo_root / hash_index[memo.uuid]["path"]
            
            try:
                if file_path and file_path.exists():
                    content = file_path.read_text(encoding='utf-8')
                    # 限制显示长度
                    if len(content) > 2000:
                        content = content[:2000] + "\n\n... (truncated)"
                else:
                    content = "File not found"
            except Exception as e:
                content = f"Error reading file: {e}"
            
            file_path_str = str(file_path) if file_path else "N/A"
            detail_text = f"""
[bold]Hash:[/bold] {memo.uuid}
[bold]ID:[/bold] {memo.id}
[bold]Title:[/bold] {memo.title}
[bold]Type:[/bold] {memo.type or 'untyped'}
[bold]Status:[/bold] {memo.status}
[bold]Created:[/bold] {memo.created_at.strftime('%Y-%m-%d %H:%M:%S') if memo.created_at else 'N/A'}
[bold]Path:[/bold] {file_path_str}
[bold]Tags:[/bold] {', '.join(memo.tags) if memo.tags else 'None'}

[bold]Content:[/bold]
{content}
"""
            detail_panel.update(detail_text)
            detail_panel.display = True
    
    def action_close_detail(self) -> None:
        """关闭详情面板（由 / 键调用）"""
        detail_panel = self.query_one("#detail-panel", Static)
        if detail_panel.display:
            # 如果详情面板显示，则关闭它
            detail_panel.display = False
            self.query_one("#file-table", DataTable).focus()
    
    def action_close_detail_or_editor(self) -> None:
        """关闭详情面板或编辑器（由 ESC 键调用）"""
        # 优先检查详情面板
        detail_panel = self.query_one("#detail-panel", Static)
        if detail_panel.display:
            self.action_close_detail()
            return
        
        # 然后检查编辑器模式
        if self._editor_mode:
            self.action_close_editor()
            return
    
    def action_close_editor(self) -> None:
        """关闭编辑器（仅在编辑器模式时有效）"""
        if not self._editor_mode:
            return
        
        # 如果是 GUI 编辑器，尝试终止进程
        if self._editor_process and self._editor_process.poll() is None:
            try:
                self._editor_process.terminate()
                self._editor_process.wait(timeout=2)
            except Exception:
                # 如果正常终止失败，强制杀死
                try:
                    self._editor_process.kill()
                except Exception:
                    pass
            finally:
                self._editor_process = None
        
        self._editor_mode = False
        self.notify("Editor closed", severity="info")
        self.action_refresh()
    
    def action_refresh(self) -> None:
        """刷新数据"""
        self.refresh_data()
        self.update_stats()
        self.update_table()
        self.notify("Data refreshed", severity="success")
    
    def action_toggle_type(self) -> None:
        """切换类型过滤"""
        types = [None, "task", "meeting", "note", "email", "untyped"]
        current_idx = types.index(self.type_filter) if self.type_filter in types else 0
        next_idx = (current_idx + 1) % len(types)
        self.type_filter = types[next_idx]
        
        if self.type_filter:
            self.notify(f"Filtering by type: {self.type_filter}", severity="info")
        else:
            self.notify("Type filter cleared", severity="info")
        
        self.apply_filters()
        self.update_table()
        self.update_stats()
    
    def action_open_editor(self) -> None:
        """使用外部编辑器打开选中的文件"""
        table = self.query_one("#file-table", DataTable)
        cursor_row = table.cursor_row
        
        if cursor_row is None or cursor_row >= len(self.filtered_files):
            self.notify("No file selected", severity="warning")
            return
        
        memo = self.filtered_files[cursor_row]
        
        # 获取文件路径
        file_path = memo.file_path
        if not file_path or not file_path.exists():
            # 尝试从 hash_index 获取路径
            hash_index = self.hash_mgr.get_index()
            if memo.uuid in hash_index:
                file_path = self.repo_root / hash_index[memo.uuid]["path"]
        
        if not file_path or not file_path.exists():
            self.notify(f"File not found: {memo.uuid}", severity="error")
            return
        
        try:
            # 检查是否是终端编辑器（vim, nano, vi 等）
            terminal_editors = ["vim", "vi", "nano", "emacs", "micro"]
            editor_base = self.editor.split()[0] if ' ' in self.editor else self.editor
            is_terminal_editor = any(editor_base.startswith(editor) for editor in terminal_editors)
            
            if is_terminal_editor:
                # 对于终端编辑器，需要同步调用并暂停 TUI
                self.notify(f"Opening {file_path.name} with {self.editor}... Press ESC to exit editor", severity="info")
                self._editor_mode = True
                # 暂停 TUI 并运行编辑器（suspend 返回一个上下文管理器）
                try:
                    with self.suspend():
                        # 使用 subprocess.run 同步执行，等待编辑完成
                        result = subprocess.run(
                            [self.editor, str(file_path)],
                            check=False  # 不抛出异常，让用户正常退出编辑器
                        )
                finally:
                    self._editor_mode = False
                # 恢复 TUI 后刷新数据，因为文件可能已被修改
                self.action_refresh()
            else:
                # 对于 GUI 编辑器（typora, code 等），异步打开
                self._editor_mode = True
                self._editor_process = subprocess.Popen(
                    [self.editor, str(file_path)], 
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.notify(f"Opening {file_path.name} with {self.editor}. Press ESC to close", severity="success")
        except Exception as e:
            self.notify(f"Failed to open editor: {e}", severity="error")
            logger.error(f"Error opening editor {self.editor}: {e}")
    
    def action_toggle_status(self) -> None:
        """切换状态过滤"""
        statuses = [None, "open", "done"]
        current_idx = statuses.index(self.status_filter) if self.status_filter in statuses else 0
        next_idx = (current_idx + 1) % len(statuses)
        self.status_filter = statuses[next_idx]
        
        if self.status_filter:
            self.notify(f"Filtering by status: {self.status_filter}", severity="info")
        else:
            self.notify("Status filter cleared", severity="info")
        
        self.apply_filters()
        self.update_table()
        self.update_stats()
    
    def _get_selected_memo(self) -> Optional[Memo]:
        """获取当前选中的文件"""
        table = self.query_one("#file-table", DataTable)
        cursor_row = table.cursor_row
        
        if cursor_row is None or cursor_row >= len(self.filtered_files):
            return None
        
        return self.filtered_files[cursor_row]
    
    def action_change_type(self) -> None:
        """切换选中文件的类型（循环切换）"""
        memo = self._get_selected_memo()
        if not memo:
            self.notify("No file selected", severity="warning")
            return
        
        # 定义类型循环顺序：untyped -> task -> meeting -> note -> email -> untyped
        type_cycle = [None, "task", "meeting", "note", "email"]
        current_type = memo.type  # 可能是 None
        
        # 找到当前类型在循环中的位置
        try:
            current_index = type_cycle.index(current_type)
            # 切换到下一个类型
            next_index = (current_index + 1) % len(type_cycle)
            new_type = type_cycle[next_index]
        except ValueError:
            # 如果当前类型不在循环中（不应该发生），默认切换到 task
            new_type = "task"
        
        # 更新类型
        try:
            if new_type is None:
                # 设置为 untyped（删除 type 字段）
                self.file_mgr.update_file(
                    memo.uuid,
                    frontmatter_updates={"type": None},
                    commit_message=f"change type to untyped"
                )
                self.notify(f"Type changed to untyped", severity="success", timeout=2.0)
            else:
                self.file_mgr.update_file(
                    memo.uuid,
                    frontmatter_updates={"type": new_type},
                    commit_message=f"change type to {new_type}"
                )
                self.notify(f"Type changed to {new_type}", severity="success", timeout=2.0)
            self.action_refresh()
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            logger.error(f"Error changing type: {e}", exc_info=True)
    
    def action_change_status(self) -> None:
        """修改选中文件的状态"""
        memo = self._get_selected_memo()
        if not memo:
            self.notify("No file selected", severity="warning")
            return
        
        # 切换状态：open <-> done
        new_status = "done" if memo.status == "open" else "open"
        
        try:
            self.file_mgr.update_file(
                memo.uuid,
                frontmatter_updates={"status": new_status},
                commit_message=f"change status from {memo.status} to {new_status}"
            )
            self.notify(f"Changed {memo.uuid} status from {memo.status} to {new_status}", severity="success")
            self.action_refresh()
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            logger.error(f"Error changing status: {e}")
    
    def action_go_top(self) -> None:
        """跳转到顶部"""
        table = self.query_one("#file-table", DataTable)
        table.cursor_row = 0
    
    def action_go_bottom(self) -> None:
        """跳转到底部"""
        table = self.query_one("#file-table", DataTable)
        if len(self.filtered_files) > 0:
            table.cursor_row = len(self.filtered_files) - 1
    
    def action_capture(self) -> None:
        """快速捕获新内容"""
        try:
            filter_input = self.query_one("#filter-input", Input)
            filter_input.placeholder = "Enter content to capture (type:task/meeting/note/email, content)..."
            filter_input.value = ""
            filter_input.remove_class("hidden")
            filter_input.focus()
            
            # 设置标记，表示这是捕获操作
            self._pending_action = ("capture", None)
            self.notify("Enter content. Format: 'type:content' or just 'content' (untyped)", severity="info", timeout=5.0)
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            logger.error(f"Error in action_capture: {e}")
    
    def action_select_area(self) -> None:
        """选择 Area 进行过滤"""
        try:
            schema = self.schema_mgr.get_schema()
            areas = getattr(schema, "areas", [])
            if not areas:
                self.notify("No areas defined in schema", severity="warning", timeout=3.0)
                return
            
            # 构建区域摘要信息
            area_summary = ", ".join(f"{area.id}:{area.name}" for area in areas)
            
            filter_input = self.query_one("#filter-input", Input)
            filter_input.placeholder = "Enter Area ID (e.g., 11) or empty for All..."
            filter_input.value = ""
            filter_input.remove_class("hidden")
            filter_input.focus()
            
            # 设置 pending_action 以在提交时处理
            self._pending_action = ("select_area", None)
            self.notify(
                f"Areas: {area_summary}",
                severity="info",
                timeout=6.0,
            )
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            logger.error(f"Error in action_select_area: {e}", exc_info=True)
    
    def action_move_file(self) -> None:
        """移动选中的文件（支持交互式选择区域和类别）"""
        memo = self._get_selected_memo()
        if not memo:
            self.notify("No file selected", severity="warning")
            return
        
        try:
            # 获取可用的区域和类别列表
            schema = self.schema_mgr.get_schema()
            areas = schema.areas
            
            # 构建简化的区域和类别提示（只显示关键信息）
            area_summary = []
            for area in areas:
                cat_names = [f"{cat.id}:{cat.name}" for cat in area.categories]
                area_summary.append(f"{area.id}({area.name}): {', '.join(cat_names)}")
            
            summary_text = " | ".join(area_summary)
            
            filter_input = self.query_one("#filter-input", Input)
            filter_input.placeholder = f"Enter: area.category (e.g., 11.1) or JD ID (e.g., AC-11.001)..."
            filter_input.value = ""
            filter_input.remove_class("hidden")
            filter_input.focus()
            
            # 设置标记，表示这是移动操作
            self._pending_action = ("move", memo)
            self.notify(
                f"Move to area.category (e.g., 11.1) or JD ID. Areas: {summary_text}",
                severity="info",
                timeout=6.0
            )
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            logger.error(f"Error in action_move_file: {e}")
    
    def action_select_category(self) -> None:
        """选择 Category 进行过滤（依赖当前 Area）"""
        try:
            if self.current_area_id is None:
                self.notify("Please select an Area first (press 'A')", severity="warning", timeout=3.0)
                return
            
            schema = self.schema_mgr.get_schema()
            area = schema.get_area(self.current_area_id)
            if not area or not area.categories:
                self.notify(
                    f"No categories defined for area {self.current_area_id}",
                    severity="warning",
                    timeout=3.0,
                )
                return
            
            # 构建类别摘要信息
            cat_summary = ", ".join(
                f"{cat.id}:{cat.name}({cat.range[0]:.3f}-{cat.range[1]:.3f})"
                for cat in area.categories
            )
            
            filter_input = self.query_one("#filter-input", Input)
            filter_input.placeholder = "Enter Category ID (e.g., 1) or empty for All..."
            filter_input.value = ""
            filter_input.remove_class("hidden")
            filter_input.focus()
            
            # 设置 pending_action
            self._pending_action = ("select_category", None)
            self.notify(
                f"Categories in Area {self.current_area_id}: {cat_summary}",
                severity="info",
                timeout=8.0,
            )
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            logger.error(f"Error in action_select_category: {e}", exc_info=True)
    
    def action_rebuild_index(self) -> None:
        """重建哈希索引"""
        try:
            from mf.commands.organize import handle_rebuild_index
            count = handle_rebuild_index(self.repo_root)
            self.notify(f"✓ Rebuilt index with {count} files", severity="success", timeout=3.0)
            # 刷新数据
            self.action_refresh()
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            logger.error(f"Error rebuilding index: {e}", exc_info=True)
    
    def action_show_list(self) -> None:
        """显示列表视图（树形）"""
        try:
            # 暂停 TUI
            with self.suspend():
                from mf.views.list_view import show_list, console
                show_list(self.repo_root, tree_format=True)
                # 等待用户按 Enter 键
                console.print("\n[dim]Press Enter to return...[/dim]")
                try:
                    input()
                except (EOFError, KeyboardInterrupt):
                    pass
            # 恢复后刷新数据
            self.action_refresh()
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            logger.error(f"Error showing list: {e}", exc_info=True)
    
    def action_show_timeline(self) -> None:
        """显示时间轴视图"""
        try:
            # 暂停 TUI
            with self.suspend():
                from mf.views.timeline_view import show_timeline, console
                show_timeline(self.repo_root, since="1 week ago", type_filter=None)
                # 等待用户按 Enter 键
                console.print("\n[dim]Press Enter to return...[/dim]")
                try:
                    input()
                except (EOFError, KeyboardInterrupt):
                    pass
            # 恢复后刷新数据
            self.action_refresh()
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            logger.error(f"Error showing timeline: {e}", exc_info=True)
    
    def action_show_calendar(self) -> None:
        """显示日历视图"""
        try:
            # 暂停 TUI
            with self.suspend():
                from mf.views.calendar_view import show_calendar, console
                show_calendar(self.repo_root, month=None, year=None, type_filter=None)
                # 等待用户按 Enter 键
                console.print("\n[dim]Press Enter to return...[/dim]")
                try:
                    input()
                except (EOFError, KeyboardInterrupt):
                    pass
            # 恢复后刷新数据
            self.action_refresh()
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            logger.error(f"Error showing calendar: {e}", exc_info=True)
    
    def action_show_schema(self) -> None:
        """显示 Schema 配置"""
        try:
            # 暂停 TUI
            with self.suspend():
                from mf.views.schema_view import show_schema, console
                show_schema(self.repo_root)
                # 等待用户按 Enter 键
                console.print("\n[dim]Press Enter to return...[/dim]")
                try:
                    input()
                except (EOFError, KeyboardInterrupt):
                    pass
            # 恢复后刷新数据（虽然 schema 显示不需要刷新，但保持一致性）
            self.action_refresh()
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
            logger.error(f"Error showing schema: {e}", exc_info=True)


def show_status_tui(repo_root: Path, editor: Optional[str] = None):
    """显示交互式 TUI 状态视图
    
    Args:
        repo_root: 仓库根目录
        editor: 外部编辑器命令（如 'typora', 'code', 'vim' 等），如果为 None 则从配置读取或自动检测
    """
    # 如果未指定编辑器，尝试从配置读取
    if editor is None:
        try:
            from mf.core.config_manager import ConfigManager
            config_mgr = ConfigManager(repo_root)
            editor = config_mgr.get_editor()
        except Exception as e:
            logger.debug(f"Failed to load editor config: {e}")
    
    app = StatusTUI(repo_root, editor=editor)
    app.run()
