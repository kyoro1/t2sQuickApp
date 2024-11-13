from flask import Flask, request, send_file, jsonify, render_template
import azure.cognitiveservices.speech as speechsdk
import io
import os
import flask  # Flaskのバージョンを確認するためにインポート

app = Flask(__name__)

# 環境変数からAzureのキーとリージョンを取得
AZURE_SPEECH_KEY = os.getenv('AZURE_SPEECH_KEY')  # 環境変数に設定することを推奨
AZURE_SERVICE_REGION = os.getenv('AZURE_SERVICE_REGION')  # 例: 'eastus'

# 使用可能な音声のマッピング
VOICE_OPTIONS = {
    'female': 'en-IN-NeerjaNeural',  # 女性のインド英語の音声
    'male': 'en-IN-PrabhatNeural'     # 男性のインド英語の音声
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/synthesize', methods=['POST'])
def synthesize():
    data = request.get_json()
    text = data.get('text', '')
    voice_choice = data.get('voice', 'female')  # デフォルトは女性の声

    if not text.strip():
        return "テキストが空です。", 400

    # 選択された声が有効か確認
    voice_name = VOICE_OPTIONS.get(voice_choice.lower())
    if not voice_name:
        return "無効な声の選択です。", 400

    try:
        # Azure Speech Configの設定
        speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SERVICE_REGION)
        speech_config.speech_synthesis_voice_name = voice_name  # 選択されたインド英語の声

        # オーディオの出力設定（メモリ上に保持）
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

        # 音声合成
        result = synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            # 音声データをバイナリとして取得
            audio_data = result.audio_data
            audio_io = io.BytesIO(audio_data)
            audio_io.seek(0)
            
            # Flaskのバージョンに応じてパラメータを設定
            flask_version = int(flask.__version__.split('.')[0])
            if flask_version >= 2:
                return send_file(
                    audio_io,
                    mimetype='audio/wav',
                    as_attachment=False,
                    download_name='output.wav'
                )
            else:
                return send_file(
                    audio_io,
                    mimetype='audio/wav',
                    as_attachment=False,
                    attachment_filename='output.wav'
                )
        else:
            return f"音声合成に失敗しました: {result.reason}", 500

    except Exception as e:
        # 詳細なエラーメッセージをログに出力
        print(f"エラーが発生しました: {str(e)}")
        return f"エラーが発生しました: {str(e)}", 500

if __name__ == '__main__':
    # 環境変数を設定していない場合は、直接キーとリージョンを設定できます（セキュリティ上推奨されません）
    # AZURE_SPEECH_KEY = "あなたのサブスクリプションキー"
    # AZURE_SERVICE_REGION = "あなたのサービスリージョン"
    app.run(host='0.0.0.0', port=5001, debug=True)
