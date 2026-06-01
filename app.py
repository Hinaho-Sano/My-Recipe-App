import streamlit as st
import csv
import os

from google import genai
from PIL import Image

st.title("マイレシピ")

#画面を「登録」と「検索」のタブに分ける
tab1, tab2 = st.tabs(["レシピを登録する", "レシピを検索する"])

#レシピ登録エリア
with tab1:
    st.header("新しいレシピの登録")

    #AIで画像読み取り
    st.subheader("写真から自動入力できるよ")
    uploaded_file = st.file_uploader("レシピの写真をアップロードしてね", type=["png", "jpg", "jpeg"])

    #初期値（最初は空っぽ）
    default_name = ""
    default_ingredients = ""
    default_steps = ""

    #もし写真がアップロードされたら
    if uploaded_file is not None:
        st.info("AIが画像を解析中...10秒ほど待ってね 🧠")
        try:
            img = Image.open(uploaded_file)
            
            #AIに画像を渡してテキストを生成する処理
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"]) #ここはあなたのAPIキーに置き換えてね！
            
            prompt = """
            添付されたレシピの画像から、以下の3つの情報を抜き出してください。
            1. 料理名 (料理のタイトルだけ)
            2. 使う材料 (材料名を「、」や「,」で区切って1行にまとめてください)
            3. 料理の手順 (ステップごとに改行して箇条書きにしてください)

            出力は必ず以下のフォーマットだけを返してください。余計な挨拶や説明は一切不要です。
            ---
            料理名: [ここに料理名]
            材料: [ここに材料]
            手順: [ここに手順]
            ---
            """
            
            #gemini-3.5-flash
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=[img, prompt]
            )
            ai_text = response.text
            
            #テキストから各項目を抜き出す処理
            for line in ai_text.split("\n"):
                if "料理名" in line:
                    default_name = line.split(":", 1)[-1].split("：", 1)[-1].strip()
                elif "材料" in line:
                    default_ingredients = line.split(":", 1)[-1].split("：", 1)[-1].strip()
                elif "手順" in line or "ステップ" in line:
                    #ここで「手順」だけでなく、残りの文章（箇条書き全体）をきれいに取り込む
                    default_steps = ai_text.split("手順")[-1].split("：")[-1].split(":")[-1].strip()
                    #前後の余計な記号をきれいに掃除
                    if default_steps.startswith("---"):
                        default_steps = default_steps.replace("---", "").strip()
                    break #手順は一番最後なのでここで処理を抜ける
                    
            st.success("AIの読み込みが完了しました！下の入力欄を確認してね✨")
            
        except Exception as e:
            st.error(f"AIの読み込み中にエラーが発生しました：{e}")
            st.warning("APIキーやモデルの設定を確認してください。")

    st.write("---") #区切り線

    #入力エリア
    new_name = st.text_input("料理名（例：ナスの麻婆豆腐）", value=default_name)
    new_ingredients = st.text_input("使う材料(例：ナス、豆腐、ひき肉)", value=default_ingredients)
    new_steps = st.text_area("料理の手順", value=default_steps, height=200)

    #登録ボタン
    submit_button = st.button("レシピを保存する")

    #ボタンが押されたら
    if submit_button:
        if not new_name or not new_ingredients or not new_steps:
            st.error("料理名、材料、手順は全部入力して〜；；")
        else:
            with open('recipe.csv', mode='a', encoding='utf-8-sig', newline='') as recipe_file:
                fieldnames = ['料理名', '食材', '手順']
                writer = csv.DictWriter(recipe_file, fieldnames=fieldnames)
                
                if os.path.exists('recipe.csv') and os.path.getsize('recipe.csv') == 0:
                    writer.writeheader()
                
                writer.writerow({
                    '料理名': new_name,
                    '食材': new_ingredients,
                    '手順': new_steps
                })
            st.success(f"「{new_name}」を保存しました〜！")
    

#レシピ検索エリア
with tab2:
    st.header("レシピを探す")
    
    #検索キーワードの入力欄（料理名でも食材でもOKにする）
    search_input = st.text_input("料理名や食材を入力してね（スペースで複数検索もできるよ）")

    #もし検索欄に文字が入力されたら
    if search_input:
        #入力された文字をスペースでバラバラにしてリストにする
        #例：「ナス 豆腐」→["ナス", "豆腐"]
        keywords = search_input.replace("　", " ").split(" ")
        
        st.subheader(f"「{ ' + '.join(keywords) }」の検索結果")

        #csvファイルを開いて検索する
        import os
        if os.path.exists('recipe.csv'):
            with open('recipe.csv', mode='r', encoding = 'utf-8-sig') as recipe_file:
                reader = csv.DictReader(recipe_file)

                match_count = 0 #見つかったレシピの数を数えるための変数

                for row in reader:
                    #検索キーワードがすべて含まれているかチェックするフラグ
                    is_match = True
                    for keyword in keywords:
                        #料理名にも食材にもそのキーワードが入っていなければ不合格
                        if (keyword not in row['料理名']) and (keyword not in row['食材']):
                            is_match = False
                            break #１つでも含まれてなければ、このレシピのチェックは終了
                    
                    #すべてのキーワードが含まれているなら、そのレシピを画面に表示
                    if is_match:
                        match_count += 1
                        st.write(f"### 🍳 {row['料理名']}")
                        st.write(f"**【使う材料】**\n{row['食材']}")

                        #改行コードをちゃんと画面に反映させる方法
                        steps_display = row['手順'].replace('\n', '\n\n')
                        st.write(f"**【料理の手順】**\n{steps_display}")
                        st.write("---") #レシピ同士を線で区切る
                    
                #一件もヒットしなかった時
                if match_count == 0:
                    st.info("見つからなかったよ〜；；")

        else:
            st.warning("まだレシピが一件も登録されていないみたい！まずは、「レシピを登録する」から始めてね！")