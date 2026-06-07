import json
from pathlib import Path
import streamlit as st

# ✅ Все файлы ищутся рядом с app.py — не важно из какой папки запускать
BASE_DIR = Path(__file__).parent
RECIPES_FILE = BASE_DIR / "recipes.json"
FAVORITES_FILE = BASE_DIR / "favorites.json"

st.set_page_config(page_title="Что приготовить?", page_icon="🍳", layout="wide")

# 🎨 Фон — стол с едой
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background-image: url("https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=1600&auto=format&fit=crop");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0, 0, 0, 0.45);
    z-index: 0;
}
[data-testid="stHeader"] { background: rgba(0,0,0,0); }
.block-container {
    position: relative;
    z-index: 1;
    background: rgba(255, 255, 255, 0.88);
    border-radius: 16px;
    padding: 2rem !important;
    margin-top: 1rem;
}
</style>
""", unsafe_allow_html=True)


def load_recipes():
    try:
        with open(RECIPES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"❌ Файл recipes.json не найден! Положи его рядом с app.py: {BASE_DIR}")
        return []


def load_favorites():
    try:
        with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_favorites(favorites):
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(favorites, f, ensure_ascii=False, indent=2)


# Инициализация состояний сессии
if "search_clicked" not in st.session_state:
    st.session_state.search_clicked = False
if "favorites" not in st.session_state:
    st.session_state.favorites = load_favorites()

recipes = load_recipes()

st.title("🍳 Что приготовить сегодня?")
st.write("Введи, что есть в холодильнике — подберём рецепты!")

tab_search, tab_favs = st.tabs(["🔍 Поиск рецептов", "❤️ Избранное"])

with tab_search:
    ingredients_input = st.text_input(
        "Ингредиенты (через запятую)",
        placeholder="яйца, помидор, сыр, хлеб, молоко",
    )

    # ✅ Исправление 4: сбрасываем поиск если поле очищено
    if not ingredients_input:
        st.session_state.search_clicked = False

    col_time, col_cat = st.columns(2)
    with col_time:
        max_time = st.slider(
            "Максимальное время приготовления (минуты)",
            min_value=5,
            max_value=90,
            value=60,
            step=5,
        )
    with col_cat:
        category = st.selectbox(
            "Категория блюда",
            ["Все", "завтрак", "обед", "ужин"],
            index=0,
        )

    if st.button("🔍 Найти рецепты", type="primary"):
        if ingredients_input:
            st.session_state.search_clicked = True
        else:
            st.warning("Сначала введите ингредиенты!")

    if st.session_state.search_clicked and ingredients_input:
        available = set(
            x.strip().lower() for x in ingredients_input.split(",") if x.strip()
        )

        matches = []
        for recipe in recipes:
            req = set(ing.lower() for ing in recipe["ingredients"])
            common = len(req & available)

            # ✅ Исправление 1: пропускаем рецепты без совпадений
            if common == 0:
                continue

            score = common / len(req) if req else 0

            # ✅ Исправление 2: пропускаем рецепт если время не парсится
            try:
                recipe_time = int(recipe["time"].split()[0])
                if recipe_time > max_time:
                    continue
            except (ValueError, IndexError):
                continue

            # Фильтр по категории
            if category != "Все" and recipe.get("category") != category:
                continue

            matches.append({"recipe": recipe, "score": score, "common": common})

        matches.sort(key=lambda x: -x["score"])
        top_matches = matches[:10]

        if not top_matches:
            st.info("Рецептов с такими параметрами не найдено 😕")
        else:
            st.subheader(f"🔥 ТОП-{len(top_matches)} рекомендаций (до {max_time} мин)")

            favorite_names = {f["name"] for f in st.session_state.favorites}

            for item in top_matches:
                r = item["recipe"]
                is_favorite = r["name"] in favorite_names

                col_name, col_btn = st.columns([5, 1])
                with col_name:
                    st.markdown(
                        f"### {r['name']} — **{r['time']}** • {r.get('category', '—')}"
                    )
                with col_btn:
                    heart = "❤️ Избранное" if is_favorite else "♡ В избранное"
                    if st.button(heart, key=f"heart_{r['name']}"):
                        if is_favorite:
                            st.session_state.favorites = [
                                f
                                for f in st.session_state.favorites
                                if f["name"] != r["name"]
                            ]
                        else:
                            st.session_state.favorites.append(r)

                        save_favorites(st.session_state.favorites)
                        st.rerun()

                st.write(
                    f"**Совпадение:** {item['common']}/{len(r['ingredients'])} ({round(item['score'] * 100)}%)"
                )
                st.write("**Ингредиенты:** " + ", ".join(r["ingredients"]))

                st.write("**📋 Пошаговое приготовление:**")
                for step in r.get("instructions", ["Нет инструкции"]):
                    st.write(f"• {step}")

                st.divider()

with tab_favs:
    st.subheader("❤️ Мои избранные рецепты")
    if st.session_state.favorites:
        for fav in st.session_state.favorites:
            col_fav_name, col_fav_del = st.columns([5, 1])
            with col_fav_name:
                st.markdown(f"### {fav['name']} — **{fav['time']}**")
            with col_fav_del:
                if st.button("🗑️ Удалить", key=f"del_{fav['name']}"):
                    st.session_state.favorites = [
                        f
                        for f in st.session_state.favorites
                        if f["name"] != fav["name"]
                    ]
                    save_favorites(st.session_state.favorites)
                    st.rerun()

            st.write("**Ингредиенты:** " + ", ".join(fav["ingredients"]))
            if "instructions" in fav:
                st.write("**Инструкция:**")
                for step in fav["instructions"]:
                    st.write(f"• {step}")
            st.divider()
    else:
        st.info("Нажимайте ♡ у рецептов, чтобы сохранить их здесь!")
