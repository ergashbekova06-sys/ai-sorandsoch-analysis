import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Сравнительный анализ классов", layout="wide")

st.title("📊 Автоматический анализ качества и успеваемости по классам")

st.write("""
Загрузите файлы с успеваемостью. Программа поддерживает:  
**Excel (.xlsx, .xls), CSV, TXT, TSV**  
Она автоматически определит нужные колонки.
""")

# ============================
# Функция чтения любого файла
# ============================

def read_any_file(file):
    name = file.name.lower()

    try:
        if name.endswith(".csv"):
            return pd.read_csv(file)
        elif name.endswith(".txt") or name.endswith(".tsv"):
            return pd.read_csv(file, delimiter="\t")
        elif name.endswith(".xlsx") or name.endswith(".xls"):
            return pd.read_excel(file)
        else:
            return None
    except Exception as e:
        st.error(f"Ошибка при чтении файла {file.name}: {e}")
        return None


# ==================================
# Загрузка файлов
# ==================================
uploaded_files = st.file_uploader(
    "Загрузите один или несколько файлов",
    type=["csv", "xlsx", "xls", "txt", "tsv"],
    accept_multiple_files=True
)

if uploaded_files:

    dfs = []
    for f in uploaded_files:
        df = read_any_file(f)
        if df is not None:
            dfs.append(df)

    if len(dfs) == 0:
        st.error("Не удалось прочитать ни один файл.")
        st.stop()

    data = pd.concat(dfs, ignore_index=True)

    # ================================================================
    # Автоматическое определение колонок
    # ================================================================

    possible_class_cols = ["class", "класс", "grade_class", "group"]
    possible_student_cols = ["student", "ученик", "fio", "name"]
    possible_grade_cols = ["grade", "оценка", "балл", "mark", "score"]

    def find_column(possible, df):
        for col in df.columns:
            if col.lower() in possible:
                return col
        return None

    col_class = find_column(possible_class_cols, data)
    col_student = find_column(possible_student_cols, data)
    col_grade = find_column(possible_grade_cols, data)

    if not col_class or not col_student or not col_grade:
        st.error("""
        Не найдены все необходимые столбцы.  
        Требуются столбцы, похожие на:  
        - class / класс  
        - student / ученик  
        - grade / оценка
        """)
        st.stop()

    # Приводим типы
    data[col_grade] = pd.to_numeric(data[col_grade], errors="coerce")
    data = data.dropna(subset=[col_grade])

    # ================================================================
    # Расчёт показателей
    # ================================================================
    report = data.groupby(col_class).agg(
        total_students=(col_student, "nunique"),
        passed=(col_grade, lambda x: sum(x >= 3)),
        quality=(col_grade, lambda x: sum(x >= 4)),
        avg_score=(col_grade, "mean")
    ).reset_index()

    report["% успеваемости"] = (report["passed"] / report["total_students"] * 100).round(1)
    report["% качества"] = (report["quality"] / report["total_students"] * 100).round(1)
    report["Средний балл"] = report["avg_score"].round(2)

    # ================================================================
    # 1) Сравнительная таблица
    # ================================================================
    st.subheader("📌 Сравнительная таблица по классам")
    st.dataframe(report)

    # ================================================================
    # 2) Диаграмма
    # ================================================================
    st.subheader("📈 Диаграмма качества и успеваемости")

    chart_data = report.set_index(col_class)[["% успеваемости", "% качества"]]
    st.bar_chart(chart_data)

    # ================================================================
    # 3) Выводы и рекомендации
    # ================================================================
    st.subheader("📝 Выводы и рекомендации")

    best_quality = report.loc[report["% качества"].idxmax()][col_class]
    worst_quality = report.loc[report["% качества"].idxmin()][col_class]

    best_success = report.loc[report["% успеваемости"].idxmax()][col_class]
    worst_success = report.loc[report["% успеваемости"].idxmin()][col_class]

    avg_q = report["% качества"].mean()
    avg_s = report["% успеваемости"].mean()

    st.markdown(f"""
    ### Общие выводы:
    - Среднее качество по школе: **{avg_q:.1f}%**  
    - Средняя успеваемость по школе: **{avg_s:.1f}%**

    ### Сильные стороны:
    - Класс с лучшим качеством знаний: **{best_quality}**
    - Класс с самой высокой успеваемостью: **{best_success}**

    ### Проблемные зоны:
    - Класс с наименьшим качеством: **{worst_quality}**
    - Класс с наименьшей успеваемостью: **{worst_success}**

    ### Рекомендации:
    - Провести индивидуальный анализ причин низкого качества у класса **{worst_quality}**.
    - Усилить работу с учащимися, имеющими оценки "2" и "3".
    - Организовать дополнительные занятия по сложным темам.
    - Провести методическое совещание для сравнения успешных практик класса **{best_quality}**.
    """)

    st.success("Анализ завершён.")
