"""
Windows SAPI による音声読み上げサービス
完全オフライン対応
"""
from typing import Optional

# SAPI SpVoice のインスタンスをキャッシュ
_voice = None

try:
    import win32com.client
    SAPI_AVAILABLE = True
except ImportError:
    SAPI_AVAILABLE = False
    print("警告: win32com が利用できません。音声読み上げ機能は使用できません。")


def _create_voice():
    """
    SAPI SpVoice を生成し、英語ボイス（Microsoft Zira Desktop）を優先的に設定する
    
    Returns:
        win32com.client.Dispatch("SAPI.SpVoice") のインスタンス
    """
    if not SAPI_AVAILABLE:
        raise RuntimeError("SAPI が利用できません")
    
    voice = win32com.client.Dispatch("SAPI.SpVoice")
    
    try:
        # ボイス一覧を取得
        voices = voice.GetVoices()
        
        # 英語ボイスを探す（特に "Microsoft Zira Desktop - English (United States)"）
        english_voice_index = None
        zira_voice_index = None
        
        for i in range(voices.Count):
            voice_item = voices.Item(i)
            description = voice_item.GetDescription()
            
            # "Microsoft Zira Desktop" を優先的に探す
            if "Zira" in description and "English" in description:
                zira_voice_index = i
                break
            # その他の英語ボイス
            elif "English" in description and english_voice_index is None:
                english_voice_index = i
        
        # 見つかったボイスを設定
        if zira_voice_index is not None:
            voice.Voice = voices.Item(zira_voice_index)
            print(f"[TTSService] 英語ボイスを設定: {voices.Item(zira_voice_index).GetDescription()}")
        elif english_voice_index is not None:
            voice.Voice = voices.Item(english_voice_index)
            print(f"[TTSService] 英語ボイスを設定: {voices.Item(english_voice_index).GetDescription()}")
        else:
            print("[TTSService] 英語ボイスが見つかりませんでした。デフォルトボイスを使用します。")
    except Exception as e:
        print(f"[TTSService] ボイス設定エラー: {e}。デフォルトボイスを使用します。")
    
    return voice


def _get_voice():
    """
    SAPI SpVoice のインスタンスを取得（キャッシュ済みの場合は再利用）
    
    Returns:
        win32com.client.Dispatch("SAPI.SpVoice") のインスタンス
    """
    global _voice
    if _voice is None:
        _voice = _create_voice()
    return _voice


def warmup() -> None:
    """SAPIをあらかじめ初期化する。音は出さない。"""
    try:
        _ = _get_voice()
    except Exception:
        pass


def speak(text: Optional[str]) -> None:
    """
    渡されたテキストをその場で読み上げる（正解時に即時再生）。
    
    Args:
        text: 読み上げるテキスト（英語）
    """
    if not text:
        return
    
    try:
        voice = _get_voice()
        voice.Speak(text)
    except Exception:
        pass


class TTSService:
    """
    後方互換性のためのラッパークラス
    """
    
    def __init__(self, voice: str = "en-GB-LibbyNeural"):
        # SAPI では voice パラメータは使用しないが、後方互換性のために保持
        self.voice = voice

    def set_voice(self, voice: str) -> None:
        """使用する TTS の voice を切り替える（SAPI では未使用だが後方互換性のため保持）。"""
        if voice:
            self.voice = voice
            print(f"[TTSService] voice changed to: {voice} (SAPI では voice 設定は無効です)")

    def get_voice(self) -> str:
        """現在の voice を取得する。"""
        return self.voice

    def warmup(self) -> None:
        """SAPIをあらかじめ初期化する（後方互換性のためのメソッド）。"""
        warmup()

    def speak(self, text: Optional[str]) -> None:
        """テキストを音声で読み上げる（後方互換性のためのメソッド）。"""
        speak(text)


# アプリ全体で共有して使うインスタンス（後方互換性のため）
tts_service = TTSService()
