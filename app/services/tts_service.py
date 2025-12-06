"""
Windows SAPI による音声読み上げサービス
完全オフライン対応
"""
try:
    import win32com.client
    SAPI_AVAILABLE = True
except ImportError:
    SAPI_AVAILABLE = False
    print("警告: win32com が利用できません。音声読み上げ機能は使用できません。")


def speak(text: str):
    """
    テキストを音声で読み上げる
    
    Args:
        text: 読み上げるテキスト（英語）
    """
    if not SAPI_AVAILABLE:
        print(f"[TTS] {text}")
        return
    
    try:
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Speak(text)
    except Exception as e:
        print(f"音声読み上げエラー: {e}")











