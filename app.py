import streamlit as st
import pandas as pd
import plotly.express as px

# ==============================
# CONFIGURAÇÃO DE SENHA
# ==============================
SENHA_CORRETA = "LEONE1234"  # troque pela sua senha

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


def formatar_moeda_br(x):
   if pd.isnull(x):
       return "-"
   return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_percentual_br(x):
    if pd.isnull(x):
        return "-"
    return f"{x:.2%}".replace(".", ",")

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

def card(titulo, valor, valor_numerico):
    
    # definir cores
    if valor_numerico < 0:
        cor_fundo = "#FFE5E5"   # vermelho claro
        cor_texto = "#B00020"   # vermelho escuro
    else:
        cor_fundo = "#E3F2FD"   # azul claro
        cor_texto = "#0D47A1"   # azul escuro

    st.markdown(f"""
    <div style="
        background:{cor_fundo};
        padding:15px;
        border-radius:10px;
        text-align:center;
        box-shadow: 0px 2px 6px rgba(0,0,0,0.2);
    ">
        <div style="font-size:13px; color:{cor_texto};">{titulo}</div>
        <div style="font-size:22px; font-weight:bold; color:{cor_texto};">
            {valor}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==============================
# FILTROS
# ==============================

st.sidebar.markdown("## 🎛️ Filtros")
st.sidebar.markdown("---")

if st.sidebar.button("🧹 Limpar Filtros"):
    st.session_state.clear()
    st.rerun()


# ==============================
# 1. PERÍODO (SAFRA)
# ==============================
sel_safra = st.sidebar.multiselect(
    "Período",
    sorted(df["SAFRA"].dropna().unique()),
    key="filtro_periodo"
)

df_temp = df.copy()

if sel_safra:
    df_temp = df_temp[df_temp["SAFRA"].isin(sel_safra)]

# ==============================
# 2. RESPONSÁVEL (depende da SAFRA)
# ==============================
resp_validos = sorted(
    df_temp[
        (df_temp["RESPONSAVEL"].notna()) &
        (df_temp["RESPONSAVEL"] != "CUSTO INTERNO")
    ]["RESPONSAVEL"].unique()
)

sel_resp = st.sidebar.multiselect(
    "Responsável",
    resp_validos,
    key="filtro_responsavel"
)

if sel_resp:
    df_temp = df_temp[df_temp["RESPONSAVEL"].isin(sel_resp)]

# ==============================
# 3. SETOR (depende do RESPONSÁVEL)
# ==============================
sel_setor = st.sidebar.multiselect(
    "Setor",
    sorted(df_temp["SETOR"].dropna().unique()),
    key="filtro_setor"
)

if sel_setor:
    df_temp = df_temp[df_temp["SETOR"].isin(sel_setor)]

# ==============================
# 4. OBRA (depende de tudo)
# ==============================
sel_obra = st.sidebar.multiselect(
    "Obra/Administrativo",
    sorted(df_temp["OBRA"].dropna().unique()),
    key="filtro_obra"
)


# ==============================
# FILTROS (ÚNICO BLOCO)
# ==============================
df_filtrado = df.copy()

if sel_safra:
    df_filtrado = df_filtrado[df_filtrado["SAFRA"].isin(sel_safra)]

if sel_resp:
    df_filtrado = df_filtrado[df_filtrado["RESPONSAVEL"].isin(sel_resp)]

if sel_setor:
    df_filtrado = df_filtrado[df_filtrado["SETOR"].isin(sel_setor)]

if sel_obra:
    df_filtrado = df_filtrado[df_filtrado["OBRA"].isin(sel_obra)]


df.columns = (
    df.columns
    .str.strip()
    .str.upper()
    .str.normalize('NFKD')
    .str.encode('ascii', errors='ignore')
    .str.decode('utf-8')
)     


id_pendente = "PENDENTE SEGMENTACAO"

pendente_selecionado = sel_resp and id_pendente in sel_resp


if pendente_selecionado:

    st.markdown("### ⚠️ Pendentes de Segmentação")
    st.markdown("---")

    df_pendente = df_filtrado.copy()

    # garantir só os pendentes
    df_pendente = df_pendente[df_pendente["RESPONSAVEL"] == id_pendente]

    # selecionar colunas desejadas
    tabela_pendente = df_pendente[[
        "Data de pagamento",
        "Nome",
        "Descrição",
        "Detalhamento",
        #"OBRA",  # centro de custo
        "CONTAS PAGAS"
    ]].rename(columns={
        "Data de pagamento": "DATA PAGAMENTO",
        "Nome": "NOME",
        "Descrição": "DESCRICAO",
        "Detalhamento": "DETALHAMENTO",
        #"OBRA": "Centro de Custo",
        "CONTAS PAGAS": "CONTAS PAGAS"
    })

    # formatação moeda
    tabela_pendente["CONTAS PAGAS"] = tabela_pendente["CONTAS PAGAS"].apply(formatar_moeda_br)

    st.dataframe(tabela_pendente, use_container_width=True, hide_index=True)

    st.stop()  # 🔥 PARA O RESTO DO DASH



# ==============================
# CARDS (TOPO)
# ==============================
st.subheader("📌 Indicadores")

total_contas_pagas = df_filtrado[df_filtrado["RESPONSAVEL"] != "CUSTO INTERNO"]["CONTAS PAGAS"].sum()
total_custo_adm = df_filtrado["CUSTO_ADM"].sum()
total_contas = total_contas_pagas + total_custo_adm
total_receita = df_filtrado["RECEITA"].sum()
resultado = total_receita + total_contas

perc_lucro = ((resultado / total_receita)) if total_contas != 0 else 0

col1, col2, col3, col4, col5, col6 = st.columns(6)



with col1: card("Contas Pagas", formatar_moeda_br(total_contas_pagas), total_contas_pagas)
with col2: card("Custo ADM", formatar_moeda_br(total_custo_adm), total_custo_adm)
with col3: card("Total Contas", formatar_moeda_br(total_contas), total_contas)
with col4: card("Receita", formatar_moeda_br(total_receita), total_receita)
with col5: card("Resultado", formatar_moeda_br(resultado), resultado)
with col6: card("% Lucro", formatar_percentual_br(perc_lucro), perc_lucro)


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


st.markdown("### 📊 Resumo por Categoria")
st.markdown("---")

tabela_categoria = df_filtrado.groupby("Categoria").agg({
    "CONTAS PAGAS": "sum",
    "CUSTO_ADM": "sum"
}).reset_index()

# formatação
tabela_categoria_fmt = tabela_categoria.copy()

tabela_categoria_fmt["CONTAS PAGAS"] = tabela_categoria_fmt["CONTAS PAGAS"].apply(formatar_moeda_br)
tabela_categoria_fmt["CUSTO_ADM"] = tabela_categoria_fmt["CUSTO_ADM"].apply(formatar_moeda_br)

tabela_categoria = tabela_categoria.sort_values(
    "Categoria"
)

st.dataframe(
    tabela_categoria_fmt,
    use_container_width=True,
    hide_index=True
)


# ==============================
# BASE DO GRÁFICO
# ==============================
df_grafico = df.copy()

if sel_resp:
    df_grafico = df_grafico[df_grafico["RESPONSAVEL"].isin(sel_resp)]

# aplicar obra
if sel_obra:
    df_grafico = df_grafico[df_grafico["OBRA"].isin(sel_obra)]


grafico = df_grafico.groupby("SAFRA").agg({
    "TOTAL_CONTAS": "sum",
    "RECEITA": "sum"
}).reset_index().sort_values("SAFRA")

grafico["RESULTADO"] = grafico["RECEITA"] + grafico["TOTAL_CONTAS"]


st.markdown("### 📊 Resultado Líquido")

grafico["cor_resultado"] = grafico["RESULTADO"].apply(
    lambda x: "#BBDEFB" if x >= 0 else "#FFCDD2"
)

grafico["texto_resultado"] = grafico["RESULTADO"].apply(formatar_moeda_br)

fig1 = px.bar(
    grafico,
    x="SAFRA",
    y="RESULTADO",
    text="texto_resultado"
)

fig1.update_traces(
    marker_color=grafico["cor_resultado"],
    textposition="auto",
textfont=dict(
    color=[
        "#0D47A1" if v >= 0 else "#B00020"
        for v in grafico["RESULTADO"]
    ],
    size=14,
    family="Arial Black"
)
)

fig1.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(t=60, b=80),
    title=dict(
        text="<b>Resultado Líquido</b>",
        font=dict(color="black", size=18)
    ),
    xaxis=dict(
        type="category",
        title="",
        tickfont=dict(
            color="black",
            size=12,
            family="Arial Black"
        )
    ),
    yaxis=dict(title="", tickfont=dict(color="black"))
)
st.plotly_chart(fig1, use_container_width=True)

st.markdown("### 💰 Receita")

grafico["texto_receita"] = grafico["RECEITA"].apply(formatar_moeda_br)

fig2 = px.bar(
    grafico,
    x="SAFRA",
    y="RECEITA",
    text="texto_receita"
)

fig2.update_traces(
    marker_color="#BBDEFB",
    textposition="auto",
    textfont=dict(
        color="#0D47A1",
        size=14,
        family="Arial Black"
    )
)

fig2.update_layout(
    margin=dict(t=60, b=80),
    plot_bgcolor="white",
    paper_bgcolor="white",
    title=dict(
        text="<b>Receita</b>",
        font=dict(color="black", size=18)
    ),
    xaxis=dict(
        type="category",
        title="",
        tickfont=dict(
            color="black",
            size=12,
            family="Arial Black"
        )
    ),
    yaxis=dict(title="", tickfont=dict(color="black"))
)

st.plotly_chart(fig2, use_container_width=True)

st.markdown("### 💸 Total Contas")

grafico["texto_contas"] = grafico["TOTAL_CONTAS"].apply(formatar_moeda_br)

fig3 = px.bar(
    grafico,
    x="SAFRA",
    y="TOTAL_CONTAS",
    text="texto_contas"
)

fig3.update_traces(
    marker_color="#FFCDD2",
    textposition="auto",
    textfont=dict(
        color="#B00020",
        size=14,
        family="Arial Black"
    )
)

fig3.update_layout(
    margin=dict(t=60, b=80),
    plot_bgcolor="white",
    paper_bgcolor="white",
    title=dict(
        text="<b>Total Contas</b>",
        font=dict(color="black", size=18)
    ),
    xaxis=dict(
        type="category",
        title="",
        tickfont=dict(
            color="black",
            size=12,
            family="Arial Black"
        )
    ),
    yaxis=dict(title="", tickfont=dict(color="black"))
)

st.plotly_chart(fig3, use_container_width=True)

