import streamlit as st
import pandas as pd
import numpy as np
import re  # <-- coloque este import lá em cima junto com os outros
import plotly.express as px
# ======================
# Estado da aplicação
# ======================

if "files_data" not in st.session_state:
    st.session_state.files_data = {}

if "active_file" not in st.session_state:
    st.session_state.active_file = None

# =========================
# Configuração da página
# =========================
st.set_page_config(
    page_title="Industrial KPI Analyzer",
    layout="wide"
)
st.markdown("## 📊 Industrial KPI Analyzer")
st.markdown(
    "<span style='color: #9FA2B4;'>Dashboard interativo para análise automática de KPIs industriais</span>", 
    unsafe_allow_html=True
)
st.markdown("""
<style>
.kpi-card {
    background-color: #1C1E26;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.25);
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.kpi-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 14px 32px rgba(0,0,0,0.35);
}

.kpi-title {
    font-size: 0.9rem;
    color: #9FA2B4;
    margin-bottom: 4px;
}

.kpi-icon {
    font-size: 1.4rem;
    margin-bottom: 6px;
}

.kpi-value {
    font-size: 1.8rem;
    font-weight: bold;
}

.kpi-green { color: #4CAF50; }
.kpi-red { color: #F44336; }
.kpi-yellow { color: #FFC107; }
.kpi-blue { color: #1E88E5; }
</style>
""", unsafe_allow_html=True)

st.markdown("---")

st.markdown(
    """
    <div style="
        background-color:#1C1E26;
        padding:16px;
        border-radius:12px;
        border-left:4px solid #1E88E5;
    ">
        Este dashboard permite analisar KPIs industriais a partir de múltiplas planilhas,
        mesmo sem padronização prévia. O sistema valida dados, detecta inconsistências
        e gera indicadores confiáveis automaticamente.
    </div>
    """,
    unsafe_allow_html=True
)

# =========================
# Funções utilitárias
# =========================

def section(title, icon=""):
    st.markdown(f"## {icon} {title}")
    st.markdown(
        "<hr style='margin-top:0.2em;margin-bottom:1em;'>",
        unsafe_allow_html=True
    )

def kpi_card(title, value, icon="📊", color="blue"):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-title">{title}</div>
            <div class="kpi-value kpi-{color}">{value}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
def to_number(series): # Converte uma série para números float, tratando diversos formatos
    def parse_value(val):
        if pd.isna(val):
            return np.nan

        # 1. Tudo vira string
        s = str(val).strip().lower()

        # 2. Valores explicitamente inválidos
        if s in ["", "nan", "none", "erro", "texto", "-", "--", "%"]:
            return np.nan

        # 3. Normalização
        s = s.replace(" ", "")
        s = s.replace(",", ".")
        s = s.replace("%", "")

        # 4. Extração do primeiro número válido
        match = re.search(r"-?\d+(\.\d+)?", s)

        if not match:
            return np.nan

        try:
            return float(match.group())
        except:
            return np.nan

    return series.apply(parse_value)


def calcular_status(valor, meta, regra):
    if pd.isna(valor):
        return "⚪ Sem dado"
    if regra == "Maior é melhor":
        return "🟢 Dentro da meta" if valor >= meta else "🔴 Fora da meta"
    else:
        return "🟢 Dentro da meta" if valor <= meta else "🔴 Fora da meta"

def format_kpi(valor, is_percent):
    if pd.isna(valor):
        return "—"

    try:
        if is_percent:
            return f"{valor:.2f}%"
        return f"{valor:,.0f}"
    except:
        return "—"
    
st.sidebar.markdown(
    """
    <div style="text-align:center;">
        <h2>⚙ Controle</h2>
        <p style="color:#9FA2B4;">Gerencie os dados da análise</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown("---")

# =========================
# Upload de arquivos (Sidebar)
# =========================

st.sidebar.markdown("## ☁️ Upload de dados")

files = st.sidebar.file_uploader(
    "Envie arquivos Excel ou CSV",
    type=["csv", "xlsx", "xls"],
    accept_multiple_files=True,
    key="file_uploader"
)

if files:
    for file in files:
        if file.name not in st.session_state.files_data:
            if file.name.lower().endswith(".csv"):
                df = pd.read_csv(
                    file,
                    sep=None,
                    engine="python",
                    encoding="latin-1",
                    dtype=str
                )
            else:
                df = pd.read_excel(file)


            df.columns = [c.strip() for c in df.columns]
            df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

            st.session_state.files_data[file.name] = df

    if st.session_state.active_file is None:
        st.session_state.active_file = list(st.session_state.files_data.keys())[0]

# =========================
# Session State - Upload
# =========================
if st.session_state.files_data:
    st.sidebar.markdown("### 📁 Planilha ativa")

    st.session_state.active_file = st.sidebar.selectbox(
        "Selecione a planilha",
        list(st.session_state.files_data.keys()),
        index=list(st.session_state.files_data.keys()).index(
            st.session_state.active_file
        )
    )
    # =========================
# Estado por planilha
# =========================
if "file_states" not in st.session_state:
    st.session_state.file_states = {}

if st.session_state.active_file not in st.session_state.file_states:
    st.session_state.file_states[st.session_state.active_file] = {}


st.sidebar.markdown("---")

if st.sidebar.button("🔄 Resetar análise"):
    st.session_state.files_data = {}
    st.session_state.active_file = None
    st.rerun()

# =========================
# Carregamento do DataFrame ativo
if st.session_state.files_data and st.session_state.active_file:
    current_df = st.session_state.files_data[st.session_state.active_file]
else:
    st.info("Envie pelo menos uma planilha para começar.")
    st.stop()

    # =========================
# Normalização defensiva (CSV / Excel)
# =========================



# 1. Remove colunas totalmente vazias
current_df = current_df.dropna(axis=1, how="all")

# 2. Remove linhas sem nenhum número (texto solto do Excel)
current_df = current_df[
    current_df.apply(lambda row: row.astype(str).str.contains(r"\d").any(), axis=1)
]

# 3. Limpa nomes de colunas
current_df.columns = (
    current_df.columns
        .astype(str)
        .str.strip()
        .str.replace("\n", " ")
)

# 4. Remove linhas explicativas tipo "Para lembrar"
current_df = current_df[
    ~current_df.apply(
        lambda r: r.astype(str).str.contains("para lembrar", case=False).any(),
        axis=1
    )
]
# ==========================
# Blindagem: nomes de colunas únicos
# ==========================
    
current_df.columns = (
    current_df.columns
    .astype(str)
    .str.strip()
)

if current_df.columns.duplicated().any():
    dup_cols = current_df.columns[current_df.columns.duplicated()].tolist()
    st.error(f"❌ Colunas duplicadas detectadas: {dup_cols}")
    st.stop()

# =========================
# Mapeamento do KPI
# =========================
section("Mapeamento do KPI", "🧭")

#  1. Colunas candidatas a tempo (PRIMEIRO!)
time_cols = [
    c for c in current_df.columns
    if "data" in c.lower() or "mês" in c.lower() or "mes" in c.lower()
]

#  2. Colunas candidatas a KPI
numeric_cols = current_df.select_dtypes(
    include=[np.number, "object"]
).columns.tolist()

if not numeric_cols:
    st.error("Não encontrei colunas utilizáveis no arquivo.")
    st.stop()

#  3. Seleção do KPI
kpi_col = st.selectbox(
    "Selecione a coluna do KPI",
    numeric_cols
)
# =========================
# Tipo de KPI (detecção automática)
# =========================

kpi_name = kpi_col.lower()

is_recovery = any(
    key in kpi_name
    for key in ["recovery", "perda", "perdas", "refugo", "scrap"]
)


#  4. Seleção da coluna de tempo
time_col = st.selectbox(
    "Selecione a coluna de tempo (opcional)",
    ["Nenhuma"] + time_cols
)

#  5. Bloqueio de segurança (AGORA FUNCIONA)
if time_col != "Nenhuma" and kpi_col == time_col:
    st.error("❌ A coluna de tempo não pode ser usada como KPI.")
    st.stop()

if is_recovery:
    kpi_rule = "Menor é melhor"
else:
    kpi_rule = st.radio(
        "Como interpretar o KPI?",
        ["Maior é melhor", "Menor é melhor"]
    )
if "meta_sugerida" not in locals():
    meta_sugerida = 0.0
#  6. Definição da meta do KPI

kpi_unit = st.selectbox(
    "Unidade do KPI",
    ["Percentual (%)", "Valor absoluto"]
)

file_state = st.session_state.file_states[st.session_state.active_file]

if kpi_unit == "Percentual (%)":
    is_percent_kpi = True

    meta_kpi = st.number_input(
        "Meta do KPI (%)",
        value=file_state.get("meta_kpi", float(meta_sugerida)),
        step=0.1,
        key=f"meta_{st.session_state.active_file}"
    )

else:
    is_percent_kpi = False

    meta_kpi = st.number_input(
        "Meta do KPI (valor)",
        value=file_state.get("meta_kpi", float(meta_sugerida)),
        step=max(1.0, meta_sugerida * 0.05),
        key=f"meta_{st.session_state.active_file}"
    )

file_state["meta_kpi"] = meta_kpi



# =========================
# Normalização do KPI
# =========================
current_df[kpi_col] = to_number(current_df[kpi_col])

# =========================
# Meta sugerida automática
# =========================

valid_values = current_df[kpi_col].dropna()

if is_recovery:
    meta_sugerida = valid_values.max() if not valid_values.empty else 0.0
else:
    meta_sugerida = valid_values.mean() if not valid_values.empty else 0.0


vals = current_df[kpi_col].dropna()

if is_percent_kpi and len(vals) > 0:
    # Se a maioria dos valores estiver entre 0 e 1, assume fração
    frac_ratio = ((vals >= 0) & (vals <= 1)).mean()

    if frac_ratio >= 0.7:
        current_df[kpi_col] = current_df[kpi_col] * 100
        st.info("🔎 KPI percentual detectado como fração (0.x). Convertido para escala % (0–100).")

# =========================
# Status do KPI
# =========================
current_df["Status KPI"] = current_df[kpi_col].apply(
    lambda x: calcular_status(x, meta_kpi, kpi_rule)
)

# ===============================
# Blindagem: nomes de colunas únicos
# ===============================
current_df.columns = (
    current_df.columns
    .astype(str)
    .str.strip()
)

if current_df.columns.duplicated().any():
    dup_cols = current_df.columns[current_df.columns.duplicated()].tolist()
    st.error(f"❌ Colunas duplicadas detectadas: {dup_cols}")
    st.stop()


# =========================
# Tratamento de tempo (robusto)
# =========================
if time_col != "Nenhuma" and time_col in current_df.columns:

    # Remove números puros que viram epoch (1970)
    current_df[time_col] = current_df[time_col].apply(
    lambda x: np.nan if str(x).strip().isdigit() else x
)
# Conversão para datetime
    current_df[time_col] = pd.to_datetime(
    current_df[time_col],
    errors="coerce",
    dayfirst=True
)


    # Tentativa 2: formato mês/ano em português (ex: fev/25)
    if current_df[time_col].isna().all():

        meses = {
            "jan": "01", "fev": "02", "mar": "03", "abr": "04",
            "mai": "05", "jun": "06", "jul": "07", "ago": "08",
            "set": "09", "out": "10", "nov": "11", "dez": "12"
        }

        def parse_mes_ano(val):
            if pd.isna(val):
                return pd.NaT
            s = str(val).lower().strip()
            for m, num in meses.items():
                if s.startswith(m):
                    return pd.to_datetime(f"20{s[-2:]}-{num}-01", errors="coerce")
            return pd.NaT

        current_df[time_col] = current_df[time_col].apply(parse_mes_ano)

# Ordenação segura
if time_col != "Nenhuma":
    chart_df = (
    current_df
    .dropna(subset=[time_col])
    .loc[current_df[time_col] >= pd.Timestamp("2000-01-01")]
    .sort_values(time_col)
)


else:
    chart_df = current_df.copy()

# =========================
# Diagnóstico dos dados
# =========================
st.subheader("🧪 Diagnóstico dos dados")

total = len(current_df)
valid_kpi = current_df[kpi_col].notna().sum()
invalid_kpi = total - valid_kpi

# Confiabilidade do dado
confiabilidade = valid_kpi / total if total > 0 else 0

with st.expander("🧪 Diagnóstico técnico dos dados", expanded=False):

    st.info(f"📊 KPI válido: {valid_kpi} de {total} registros")
    st.info(f"🔍 Confiabilidade do KPI: {confiabilidade:.0%}")

    if confiabilidade >= 0.8:
        st.success("🟢 Alta confiabilidade dos dados")
    elif confiabilidade >= 0.5:
        st.warning("🟡 Confiabilidade moderada dos dados")
    else:
        st.error("🔴 Baixa confiabilidade dos dados")

    if invalid_kpi > 0:
        st.warning(
            f"⚠️ {invalid_kpi} registros do KPI foram ignorados por dados inválidos"
        )

if time_col != "Nenhuma":
    valid_dates = current_df[time_col].notna().sum()

    if valid_dates == 0:
        st.warning("⚠️ Nenhuma data válida detectada. Gráfico temporal desativado.")
    else:
        st.info(f"📅 Datas válidas: {valid_dates} de {total}")

# =========================
# Métricas principais
# =========================
# KPI Atual correto (último valor válido)
serie_valida = chart_df.dropna(subset=[kpi_col])

if time_col != "Nenhuma" and time_col in chart_df.columns:
    serie_valida = chart_df.dropna(subset=[kpi_col, time_col]).sort_values(time_col)

kpi_atual = serie_valida[kpi_col].iloc[-1] if not serie_valida.empty else np.nan

ultimos_validos = serie_valida[kpi_col].tail(5)

kpi_operacional = (
    ultimos_validos.mean()
    if len(ultimos_validos) >= 3
    else np.nan
)

media_kpi = chart_df[kpi_col].mean()
minimo = chart_df[kpi_col].min()
fora_meta = (current_df["Status KPI"] == "🔴 Fora da meta").sum()

# Tendência
tendencia = "→ Estável"
if len(chart_df[kpi_col].dropna()) >= 6:
    recente = chart_df[kpi_col].dropna().tail(3).mean()
    anterior = chart_df[kpi_col].dropna().iloc[:-3].tail(3).mean()
    if recente > anterior:
        tendencia = "↑ Melhorando"
    elif recente < anterior:
        tendencia = "↓ Piorando"

# =========================
# Visão Executiva
# =========================
section("Visão Executiva", "📌")

c1, c2, c3, c4 = st.columns(4)

# Cor por status
status_color = "green" if "Dentro" in current_df["Status KPI"].iloc[-1] else "red"

# Cor por status
status = current_df["Status KPI"].iloc[-1]
status_color = "green" if "Dentro" in status else "red"

# Cor por tendência
if "↑" in tendencia:
    trend_color = "green"
elif "↓" in tendencia:
    trend_color = "red"
else:
    trend_color = "yellow"


with c1:
    kpi_card(
        "KPI Atual",
        format_kpi(kpi_atual, is_percent_kpi),
        "📊",
        status_color
    )

with c2:
    kpi_card(
    "Meta",
    format_kpi(meta_kpi, is_percent_kpi),

    "🎯",
    "blue"
)
    
with c3:
    kpi_card(
        "Status",
        status,
        "🚦",
        status_color
    )

with c4:
    kpi_card(
        "Tendência",
        tendencia,
        "📉",
        trend_color
    )

st.subheader("🧪 Diagnóstico dos dados")

st.info(f"📊 KPI válido: {valid_kpi} de {total} registros")
st.info(f"🔍 Confiabilidade do KPI: {confiabilidade:.0%}")

if confiabilidade >= 0.8:
    st.success("🟢 Alta confiabilidade dos dados")
elif confiabilidade >= 0.5:
    st.warning("🟡 Confiabilidade moderada dos dados")
else:
    st.error("🔴 Baixa confiabilidade dos dados")

st.caption(
    "ℹ️ Registros inválidos foram ignorados automaticamente para garantir maior confiabilidade da análise."
)
# =========================
# KPIs adicionais
# =========================
c1, c2, c3, c4 = st.columns(4)
c1.metric("Meta", format_kpi(meta_kpi, is_percent_kpi))
c2.metric("Média", format_kpi(media_kpi, is_percent_kpi))
c3.metric("Mínimo", format_kpi(minimo, is_percent_kpi))
c4.metric("Registros fora da meta", fora_meta)

# =========================
# Preparação para exibição (display)
# =========================
display_df = current_df.copy()

if time_col != "Nenhuma" and time_col in display_df.columns:
    display_df[time_col] = display_df[time_col].dt.strftime("%Y-%m-%d")

    st.subheader("📄 Dados utilizados na análise")
st.caption("Somente registros válidos foram considerados nos cálculos.")

# =========================
# Tabela
# =========================
section("Dados Consolidados", "📄")


# Colunas opcionais (texto / observações)
optional_cols = ["Para lembrar:", "observações", "Observações"]

df_table = current_df.copy()

# =========================
# Ajuste de exibição numérica (auditoria)
# =========================
numeric_cols = df_table.select_dtypes(include=["number"]).columns

for col in numeric_cols:
    df_table[col] = df_table[col].round(0)

# =========================
# Remove colunas opcionais sem conteúdo
# =========================
for col in optional_cols:
    if col in df_table.columns:
        if df_table[col].isna().all():
            df_table = df_table.drop(columns=[col])


st.dataframe(
    df_table,
    use_container_width=True
)

# =========================
# Gráfico
# =========================
if (
    time_col != "Nenhuma"
    and time_col in chart_df.columns
    and chart_df[time_col].notna().sum() > 0
):
    section("Evolução do KPI", "📈")

    plot_df = (
    chart_df[[time_col, kpi_col]]
    .dropna(subset=[time_col, kpi_col])
    .sort_values(time_col)
    .set_index(time_col)
)

    last_year = plot_df.index.max().year

    full_range = pd.date_range(
    start=plot_df.index.min(),
    end=pd.Timestamp(year=last_year, month=12, day=1),
    freq="MS"
)

    plot_df = plot_df.reindex(full_range)


    if not plot_df.empty:
        fig = px.line(
        plot_df,
    x=plot_df.index,
    y=kpi_col,
    markers=True,
    title="Evolução do KPI ao longo do tempo"
)

#  eixo mensal correto (SEM datas fantasmas)
        fig.update_xaxes(
    type="date",
    tickformat="%b/%Y",
    dtick="M1",
    ticklabelmode="period",
    range=[
        plot_df.index.min(),
        plot_df.index.max()
    ]
)


        fig.add_hline(
    y=meta_kpi,
    line_dash="dash",
    line_color="red",
    annotation_text="Meta",
    annotation_position="top right"
)

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("ℹ️ Dados insuficientes para gerar gráfico temporal.")

        section("Comparação do KPI por Período", "📊")
        

# Preparar dados (últimos N meses)
bar_df = (
    chart_df[[time_col, kpi_col]]
    .dropna(subset=[time_col, kpi_col])
    .sort_values(time_col)
    .tail(6)  # últimos 6 períodos
)

if kpi_rule == "Maior é melhor":
    bar_df["Status"] = bar_df[kpi_col].apply(
        lambda x: "Dentro da meta" if x >= meta_kpi else "Fora da meta"
    )
else:  # Menor é melhor (recovery, perdas, defeitos)
    bar_df["Status"] = bar_df[kpi_col].apply(
        lambda x: "Dentro da meta" if x <= meta_kpi else "Fora da meta"
    )


if not bar_df.empty:

    fig_bar = px.bar(
        bar_df,
        x=time_col,
        y=kpi_col,
        color="Status",
        color_discrete_map={
            "Dentro da meta": "#4CAF50",
            "Fora da meta": "#F44336"
        },
        template="plotly_dark",
        text_auto=".2f"
    )

    fig_bar.update_traces(
        customdata=bar_df[["Status"]].values,
        hovertemplate=
            "<b>Período:</b> %{x}<br>"
            "<b>KPI:</b> %{y:.2f}<br>"
            f"<b>Meta:</b> {meta_kpi:.2f}<br>"
            "<b>Status:</b> %{customdata[0]}"
            "<extra></extra>"
    )

    fig_bar.add_hline(
        y=meta_kpi,
        line_dash="dash",
        line_color="red",
        annotation_text="Meta",
        annotation_position="top right"
    )

    fig_bar.update_layout(
        title="KPI por período (comparação direta)",
        title_x=0.5,
        yaxis_title="Valor do KPI",
        xaxis_title="Período",
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig_bar, use_container_width=True)

else:
    st.info("📉 Dados insuficientes para exibir gráfico de colunas.")




