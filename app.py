import streamlit as st
import pandas as pd

# ==============================
# CONFIGURAÇÃO DE SENHA
# ==============================
SENHA_CORRETA = "LEONI1234"  # troque pela sua senha

if "logado" not in st.session_state:
    st.session_state.logado = False

# ==============================
# TELA DE LOGIN
# ==============================
if not st.session_state.logado:

    st.title("🔐 Acesso Restrito")

    senha = st.text_input("Digite a senha", type="password")

    if st.button("Entrar"):
        if senha == SENHA_CORRETA:
            st.session_state.logado = True
            st.rerun()
        else:
            st.error("Senha incorreta")

    st.stop()  # 🔥 trava o resto do código

# ==============================
# SE PASSOU DAQUI → LIBERADO
# ==============================


st.set_page_config(layout="wide")

st.title("📊 Dashboard Financeiro")

# ==============================
# CARREGAR BASE (AGORA CORRETO)
# ==============================
df = pd.read_excel("PAINEL.xlsx")

# ==============================
# RENOMEAR COLUNAS
# ==============================
df = df.rename(columns={
    "Centro de Custo": "OBRA",
    "CUSTO INTERNO": "CUSTO_ADM"
})

# ==============================
# TRATAMENTO NUMÉRICO CORRETO
# ==============================
def tratar_numero(col):
    # se já for número, mantém
    if pd.api.types.is_numeric_dtype(col):
        return col
    
    # se for texto, trata
    return pd.to_numeric(
        col.astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce"
    )

for col in ["CONTAS PAGAS", "CUSTO_ADM", "RECEITA"]:
    df[col] = tratar_numero(df[col])


# ==============================
# CÁLCULOS
# ==============================
df["TOTAL_CONTAS"] = df["CONTAS PAGAS"] + df["CUSTO_ADM"]
df["RESULTADO_LIQUIDO"] = df["RECEITA"] - df["TOTAL_CONTAS"]
df["% LUCRO"] = df["RESULTADO_LIQUIDO"] / df["TOTAL_CONTAS"]

# ==============================
# FILTROS
# ==============================
st.sidebar.header("🎛️ Filtros")

sel_safra = st.sidebar.multiselect(
    "Safra",
    df["SAFRA"].dropna().unique()
)


# ==============================
# FILTRO RESPONSÁVEL
# ==============================
sel_resp = st.sidebar.multiselect(
    "Responsável",
    sorted(
        df[
            (df["RESPONSAVEL"].notna()) &
            (df["RESPONSAVEL"] != "CUSTO INTERNO")
        ]["RESPONSAVEL"].unique()
    ),
    key="filtro_responsavel"
)


# ==============================
# FILTRO OBRA (DINÂMICO)
# ==============================
if sel_resp:
    df_temp = df[df["RESPONSAVEL"].isin(sel_resp)]
else:
    df_temp = df

sel_obra = st.sidebar.multiselect(
    "Obra",
    sorted(df_temp["OBRA"].dropna().unique()),
    key="filtro_obra"
)

# ==============================
# FILTROS (ÚNICO BLOCO)
# ==============================
df_filtrado = df.copy()

# SAFRA
if sel_safra:
    df_filtrado = df_filtrado[df_filtrado["SAFRA"].isin(sel_safra)]

# RESPONSÁVEL
if sel_resp:
    df_filtrado = df_filtrado[df_filtrado["RESPONSAVEL"].isin(sel_resp)]

# OBRA
if sel_obra:
    df_filtrado = df_filtrado[df_filtrado["OBRA"].isin(sel_obra)]

# ==============================
# CARDS (TOPO)
# ==============================
st.subheader("📌 Indicadores")

total_contas_pagas = df_filtrado["CONTAS PAGAS"].sum()
total_custo_adm = df_filtrado["CUSTO_ADM"].sum()
total_contas = total_contas_pagas + total_custo_adm
total_receita = df_filtrado["RECEITA"].sum()
resultado = total_receita + total_contas

perc_lucro = ((resultado / total_receita)) if total_contas != 0 else 0

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Contas Pagas", f"R$ {total_contas_pagas:,.0f}")
col2.metric("Custo ADM", f"R$ {total_custo_adm:,.0f}")
col3.metric("Total Contas", f"R$ {total_contas:,.0f}")
col4.metric("Receita", f"R$ {total_receita:,.0f}")
col5.metric("Resultado", f"R$ {resultado:,.0f}")
col6.metric("% Lucro", f"{perc_lucro:.2%}")

# ==============================
# TABELA
# ==============================

def cor_negativa(val):
    try:
        if pd.isnull(val):
            return ""

        # Se for string (moeda ou %)
        if isinstance(val, str):
            val = (
                val.replace("R$", "")
                   .replace("%", "")
                   .replace(".", "")
                   .replace(",", ".")
                   .strip()
            )
            val = float(val)

            # se era percentual (ex: 12.34 vira 0.1234)
            if "%" in str(val):
                val = val / 100

        if val < 0:
            return "color: red; font-weight: bold"
    except:
        pass

    return ""


st.subheader("📋 Detalhamento por Obra")

def formatar_moeda_br(x):
    if pd.isnull(x):
        return "-"
    return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_percentual_br(x):
    if pd.isnull(x):
        return "-"
    return f"{x:.2%}".replace(".", ",")

tabela = df_filtrado.groupby("OBRA").agg({
    "CONTAS PAGAS": "sum",
    "CUSTO_ADM": "sum",
    "TOTAL_CONTAS": "sum",
    "RECEITA": "sum"
    }).reset_index()

tabela["RESULTADO_LIQUIDO"] = tabela["CONTAS PAGAS"] + tabela["CUSTO_ADM"] + tabela["RECEITA"]
tabela["RECEITA_AJUSTADA"] = tabela["RECEITA"].replace(0, 0.001)

tabela["% LUCRO"] = tabela["RESULTADO_LIQUIDO"] / tabela["RECEITA_AJUSTADA"]

# TOTAL
#total = tabela.sum(numeric_only=True)
#total["OBRA"] = "TOTAL"

#tabela = pd.concat([tabela, pd.DataFrame([total])], ignore_index=True)

tabela = tabela.drop(columns=["RECEITA_AJUSTADA"], errors="ignore")

# ==============================
# FORMATAÇÃO
# ==============================
def formatar_moeda(x):
    return f"R$ {x:,.2f}"

def formatar_percentual(x):
    return f"{x:.2%}"

tabela_formatada = tabela.copy()

colunas_moeda = [
    "CONTAS PAGAS",
    "CUSTO_ADM",
    "TOTAL_CONTAS",
    "RECEITA",
    "RESULTADO_LIQUIDO"
]

for col in colunas_moeda:
    tabela_formatada[col] = tabela_formatada[col].apply(formatar_moeda_br)

tabela_formatada["% LUCRO"] = tabela_formatada["% LUCRO"].apply(formatar_percentual_br)

styled = tabela_formatada.style.applymap(
    cor_negativa,
    subset=["RESULTADO_LIQUIDO", "% LUCRO"]
)

# ==============================
# ESTILO (CSS)
# ==============================
st.markdown("""
<style>
thead tr th {
    text-align: center !important;
    font-size: 16px !important;
}

tbody tr td {
    text-align: center !important;
    font-size: 15px !important;
    padding: 6px !important;
}

table {
    width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# EXIBIÇÃO
# ==============================
tabela_exibicao = tabela.drop(columns=["RECEITA_AJUSTADA"], errors="ignore")

st.dataframe(
    styled,
    use_container_width=True,
    hide_index=True
)


# ==============================
# BASE DO GRÁFICO
# ==============================
df_grafico = df.copy()

# NÃO aplicar filtro de safra (como você pediu)

# aplicar responsável
if sel_resp:
    df_grafico = df_grafico[df_grafico["RESPONSAVEL"].isin(sel_resp)]

# aplicar obra
if sel_obra:
    df_grafico = df_grafico[df_grafico["OBRA"].isin(sel_obra)]


grafico = df_grafico.groupby("SAFRA").agg({
    "TOTAL_CONTAS": "sum",
    "RECEITA": "sum"
}).reset_index()

import plotly.express as px

st.subheader("📊 Evolução por Safra")

fig = px.bar(
    grafico,
    x="SAFRA",
    y=["TOTAL_CONTAS", "RECEITA"],
    barmode="group",
    text_auto=True
)

st.plotly_chart(fig, use_container_width=True)


