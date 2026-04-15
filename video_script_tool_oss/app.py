from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from core import DEFAULT_LANGS, ExtractionError, extract_bilibili_transcript


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("B站视频文案提取工具")
        self.geometry("980x760")
        self.minsize(860, 680)

        self.log_queue: "queue.Queue[str]" = queue.Queue()
        self.result_queue: "queue.Queue[str]" = queue.Queue()
        self.worker: threading.Thread | None = None

        self.url_var = tk.StringVar()
        self.output_var = tk.StringVar(value=str((Path.cwd() / "outputs").resolve()))
        self.lang_var = tk.StringVar(value=DEFAULT_LANGS)
        self.cookie_var = tk.StringVar()
        self.transcribe_var = tk.BooleanVar(value=True)
        self.model_var = tk.StringVar(value="small")
        self.device_var = tk.StringVar(value="auto")

        self._build_ui()
        self.after(200, self._drain_queues)

    def _build_ui(self) -> None:
        pad = {"padx": 12, "pady": 8}

        form = ttk.Frame(self)
        form.pack(fill="x", padx=16, pady=16)

        ttk.Label(form, text="B站链接").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(form, textvariable=self.url_var).grid(row=0, column=1, columnspan=3, sticky="ew", **pad)

        ttk.Label(form, text="输出目录").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(form, textvariable=self.output_var).grid(row=1, column=1, columnspan=2, sticky="ew", **pad)
        ttk.Button(form, text="选择", command=self.choose_output).grid(row=1, column=3, sticky="ew", **pad)

        ttk.Label(form, text="Cookies 文件（可选）").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(form, textvariable=self.cookie_var).grid(row=2, column=1, columnspan=2, sticky="ew", **pad)
        ttk.Button(form, text="选择", command=self.choose_cookie).grid(row=2, column=3, sticky="ew", **pad)

        ttk.Label(form, text="字幕语言优先级").grid(row=3, column=0, sticky="w", **pad)
        ttk.Entry(form, textvariable=self.lang_var).grid(row=3, column=1, columnspan=3, sticky="ew", **pad)

        options = ttk.Frame(form)
        options.grid(row=4, column=0, columnspan=4, sticky="ew", padx=12, pady=8)
        options.columnconfigure(1, weight=1)
        options.columnconfigure(3, weight=1)

        ttk.Checkbutton(
            options, text="无字幕时自动转写", variable=self.transcribe_var
        ).grid(row=0, column=0, sticky="w", padx=4)
        ttk.Label(options, text="Whisper 模型").grid(row=0, column=1, sticky="e", padx=4)
        ttk.Combobox(
            options,
            textvariable=self.model_var,
            values=["tiny", "base", "small", "medium", "large-v3"],
            state="readonly",
            width=12,
        ).grid(row=0, column=2, sticky="w", padx=4)
        ttk.Label(options, text="设备").grid(row=0, column=3, sticky="e", padx=4)
        ttk.Combobox(
            options,
            textvariable=self.device_var,
            values=["auto", "cpu", "cuda"],
            state="readonly",
            width=10,
        ).grid(row=0, column=4, sticky="w", padx=4)

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", padx=16)
        self.start_btn = ttk.Button(buttons, text="开始提取", command=self.start_extract)
        self.start_btn.pack(side="left")
        ttk.Button(buttons, text="打开输出目录", command=self.open_output_dir).pack(side="left", padx=8)
        ttk.Button(buttons, text="清空结果", command=self.clear_text).pack(side="left")

        mid = ttk.Panedwindow(self, orient=tk.VERTICAL)
        mid.pack(fill="both", expand=True, padx=16, pady=16)

        log_frame = ttk.Labelframe(mid, text="运行日志")
        self.log_text = tk.Text(log_frame, height=12, wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        mid.add(log_frame, weight=1)

        transcript_frame = ttk.Labelframe(mid, text="提取结果")
        self.result_text = tk.Text(transcript_frame, wrap="word")
        self.result_text.pack(fill="both", expand=True, padx=10, pady=10)
        mid.add(transcript_frame, weight=3)

        form.columnconfigure(1, weight=1)
        form.columnconfigure(2, weight=1)

    def choose_output(self) -> None:
        chosen = filedialog.askdirectory(initialdir=self.output_var.get() or str(Path.cwd()))
        if chosen:
            self.output_var.set(chosen)

    def choose_cookie(self) -> None:
        chosen = filedialog.askopenfilename(filetypes=[("Text", "*.txt"), ("All files", "*.*")])
        if chosen:
            self.cookie_var.set(chosen)

    def open_output_dir(self) -> None:
        path = Path(self.output_var.get()).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        try:
            import os

            os.startfile(path)  # type: ignore[attr-defined]
        except Exception:
            messagebox.showinfo("输出目录", str(path))

    def clear_text(self) -> None:
        self.log_text.delete("1.0", tk.END)
        self.result_text.delete("1.0", tk.END)

    def log(self, message: str) -> None:
        self.log_queue.put(message)

    def set_result(self, text: str) -> None:
        self.result_queue.put(text)

    def _drain_queues(self) -> None:
        while not self.log_queue.empty():
            line = self.log_queue.get_nowait()
            self.log_text.insert(tk.END, line + "\n")
            self.log_text.see(tk.END)

        if not self.result_queue.empty():
            result = self.result_queue.get_nowait()
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, result)
            self.result_text.see(tk.END)

        self.after(200, self._drain_queues)

    def start_extract(self) -> None:
        if self.worker and self.worker.is_alive():
            messagebox.showwarning("忙", "当前已有任务在运行。")
            return
        self.start_btn.configure(state="disabled")
        self.result_text.delete("1.0", tk.END)
        self.log("=" * 40)
        self.log("开始任务")
        self.worker = threading.Thread(target=self._run_task, daemon=True)
        self.worker.start()

    def _run_task(self) -> None:
        try:
            result = extract_bilibili_transcript(
                url=self.url_var.get().strip(),
                output_dir=self.output_var.get().strip(),
                preferred_langs=self.lang_var.get().strip(),
                transcribe_when_needed=self.transcribe_var.get(),
                whisper_model=self.model_var.get(),
                device=self.device_var.get(),
                cookiefile=self.cookie_var.get().strip() or None,
                log=self.log,
            )
            self.set_result(result.transcript_text)
            self.log(f"完成，来源：{result.source}")
            if result.transcript_path:
                self.log(f"文稿保存：{result.transcript_path}")
            if result.raw_subtitle_path:
                self.log(f"原始字幕：{result.raw_subtitle_path}")
            if result.audio_path:
                self.log(f"音频文件：{result.audio_path}")
        except ExtractionError as exc:
            self.log(f"失败：{exc}")
            error_message = str(exc)
            self.after(0, lambda: messagebox.showerror("提取失败", error_message))
        except Exception as exc:
            self.log(f"未预期错误：{exc}")
            error_message = str(exc)
            self.after(0, lambda: messagebox.showerror("错误", error_message))
        finally:
            self.after(0, lambda: self.start_btn.configure(state="normal"))


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
