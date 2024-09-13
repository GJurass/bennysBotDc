import discord
from discord.ext import commands
from discord.ui import Button, View

# Configurações básicas do bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Dicionário para armazenar os valores e mensagens de cada usuário
user_sessions = {}
user_discount = {}
user_full_tuning_selected = {}
user_selected_items = {}
user_messages = {}

# Canal específico do servidor (substitua pelo ID do canal que deseja usar)
SERVER_CHANNEL_ID = 1283483414372155422  # Substitua pelo ID do seu canal


# Função para adicionar valor ao total do usuário
def adicionar_valor(user_id, valor):
    if user_id not in user_sessions:
        user_sessions[user_id] = 0
    user_sessions[user_id] += valor


# Função para subtrair valor ao total do usuário
def remover_valor(user_id, valor):
    if user_id in user_sessions:
        user_sessions[user_id] -= valor


# Função para definir o desconto
def definir_desconto(user_id, desconto):
    user_discount[user_id] = desconto


# Função para calcular o valor final com desconto
def aplicar_desconto(user_id, valor_total):
    desconto = user_discount.get(user_id, 0)
    return valor_total - (valor_total * desconto / 100)


# Função para enviar a interface de seleção para o canal do servidor
async def start_user_session(user, channel):
    user_full_tuning_selected[user.id] = False  # Reseta seleção de full tuning para o usuário
    user_selected_items[user.id] = []  # Reseta os itens selecionados
    user_discount[user.id] = 0  # Reseta o desconto
    user_messages[user.id] = []  # Reseta as mensagens do usuário

    # Funções de callback para cada botão
    async def tunagem_callback(interaction, valor, button, view, item):
        # Verifica se o botão já está desabilitado (selecionado)
        if button.style == discord.ButtonStyle.primary:  # Verifica se está habilitado
            if user_full_tuning_selected.get(interaction.user.id, False):
                await interaction.response.send_message(
                    "Você já selecionou uma opção de Full Tuning. Só é permitido uma.", ephemeral=True)
            else:
                adicionar_valor(interaction.user.id, valor)
                button.style = discord.ButtonStyle.danger  # Muda a cor para mostrar que foi selecionado
                user_full_tuning_selected[interaction.user.id] = True  # Marca como selecionado
                user_selected_items[interaction.user.id].append(item)  # Adiciona o item selecionado
        else:
            remover_valor(interaction.user.id, valor)
            button.style = discord.ButtonStyle.primary  # Volta a cor original
            user_full_tuning_selected[interaction.user.id] = False  # Marca como não selecionado
            user_selected_items[interaction.user.id].remove(item)  # Remove o item selecionado
        await interaction.response.edit_message(view=view)

    async def finalizar_callback(interaction):
        total = user_sessions.get(interaction.user.id, 0)
        total_com_desconto = aplicar_desconto(interaction.user.id, total)
        itens_comprados = ', '.join(user_selected_items.get(interaction.user.id, []))

        # Enviar a mensagem com o valor total e os itens comprados
        await interaction.response.send_message(
            f"Valor total com desconto: {total_com_desconto:.2f} R$\nItens comprados: {itens_comprados}",
            ephemeral=True)

        # Excluir todas as mensagens do usuário
        for msg in user_messages[interaction.user.id]:
            try:
                await msg.delete()
            except Exception as e:
                print(f"Erro ao excluir mensagem: {e}")

        # Reseta tudo e inicia o processo novamente
        user_sessions[interaction.user.id] = 0  # Reseta após finalizar
        user_discount[interaction.user.id] = 0  # Reseta o desconto também
        user_full_tuning_selected[interaction.user.id] = False  # Reseta seleção de Full Tuning
        user_selected_items[interaction.user.id] = []  # Reseta os itens selecionados
        await start_user_session(interaction.user, interaction.channel)  # Reinicia o processo

    # Função de callback para modificações
    async def modificacao_callback(interaction, valor, button, view, item):
        # Verifica se o botão já está desabilitado (selecionado)
        if button.style == discord.ButtonStyle.secondary:  # Verifica se está habilitado
            adicionar_valor(interaction.user.id, valor)
            button.style = discord.ButtonStyle.danger  # Muda a cor para mostrar que foi selecionado
            user_selected_items[interaction.user.id].append(item)  # Adiciona o item selecionado
        else:
            remover_valor(interaction.user.id, valor)
            button.style = discord.ButtonStyle.secondary  # Volta a cor original
            user_selected_items[interaction.user.id].remove(item)  # Remove o item selecionado
        await interaction.response.edit_message(view=view)

    # Função de callback para o desconto (agora permitindo deseleção)
    async def desconto_callback(interaction, desconto, button, view):
        if user_discount[interaction.user.id] == desconto:  # Se o desconto já foi selecionado, desmarcar
            user_discount[interaction.user.id] = 0
            button.style = discord.ButtonStyle.primary  # Voltar para o estilo inicial
        else:
            user_discount[interaction.user.id] = desconto
            button.style = discord.ButtonStyle.danger  # Mudar a cor para mostrar que foi selecionado
        await interaction.response.edit_message(view=view)  # Atualizar a mensagem

    # Criando views e botões de tunagem de motos
    view_motos = View()
    button_moto_full_blindagem = Button(label="Full Tuning (Blindagem)", style=discord.ButtonStyle.primary)
    button_moto_full_blindagem.callback = lambda interaction: tunagem_callback(interaction, 170000,
                                                                               button_moto_full_blindagem, view_motos,
                                                                               "Full Tuning (Blindagem) - Moto")

    button_moto_full_sem_blindagem = Button(label="Full Tuning (Sem Blindagem)", style=discord.ButtonStyle.primary)
    button_moto_full_sem_blindagem.callback = lambda interaction: tunagem_callback(interaction, 120000,
                                                                                   button_moto_full_sem_blindagem,
                                                                                   view_motos,
                                                                                   "Full Tuning (Sem Blindagem) - Moto")

    view_motos.add_item(button_moto_full_blindagem)
    view_motos.add_item(button_moto_full_sem_blindagem)

    # Criando views e botões de tunagem de carros
    view_carros = View()
    button_carro_full_blindagem = Button(label="Full Tuning (Blindagem)", style=discord.ButtonStyle.primary)
    button_carro_full_blindagem.callback = lambda interaction: tunagem_callback(interaction, 200000,
                                                                                button_carro_full_blindagem,
                                                                                view_carros,
                                                                                "Full Tuning (Blindagem) - Carro")

    button_carro_full_sem_blindagem = Button(label="Full Tuning (Sem Blindagem)", style=discord.ButtonStyle.primary)
    button_carro_full_sem_blindagem.callback = lambda interaction: tunagem_callback(interaction, 150000,
                                                                                    button_carro_full_sem_blindagem,
                                                                                    view_carros,
                                                                                    "Full Tuning (Sem Blindagem) - Carro")

    view_carros.add_item(button_carro_full_blindagem)
    view_carros.add_item(button_carro_full_sem_blindagem)

    # Configurando os botões de modificações (com valores corretos, mas sem exibir no botão)
    modificacoes = [
        ("Aerofólio", 5000), ("Parachoque Frontal", 5000), ("Parachoque Traseiro", 5000),
        ("Escapamento", 5000), ("Gaiola", 5000), ("Grelha", 5000), ("Capo", 5000),
        ("Buzinas", 5000), ("Enfeites", 5000), ("Ponteiros", 5000),
        ("Placas (Interior)", 5000), ("Design", 5000), ("Volante", 5000), ("Câmbio", 5000),
        ("Som", 5000), ("Porta-Malas", 5000), ("Farol Xenon", 15000), ("Decal", 15000),
        ("Roda", 15000), ("Cor Roda", 5000), ("Rodas Custom", 5000), ("Roda Drift", 5000),
        ("Blindagem Roda", 5000), ("Fumaça", 5000), ("Placa Design", 5000),
        ("Placa Custom", 5000), ("Kit Neon", 5000), ("Vidro", 5000),
        ("Bloco do Motor", 5000), ("Filtro de Ar", 5000), ("Cor Metálica", 8000),  ("Perolado", 8000),
        ("Cor cromada", 8000), ("Cor Fosca", 8000), ("Cor Metal", 8000),  ("Cor RGB", 8000)
    ]

    # Dividindo os botões de modificações em múltiplas views, com no máximo 25 botões por view
    views_modificacoes = []
    for i in range(0, len(modificacoes), 25):
        view = View()
        for mod, valor in modificacoes[i:i + 25]:
            button = Button(label=mod, style=discord.ButtonStyle.secondary)
            button.callback = lambda interaction, valor=valor, button=button, view=view, item=mod: modificacao_callback(
                interaction, valor, button, view, mod)
            view.add_item(button)
        views_modificacoes.append(view)

    # Criando view e botões de desconto
    view_descontos = View()
    button_sem_desconto = Button(label="Sem Desconto", style=discord.ButtonStyle.primary)
    button_sem_desconto.callback = lambda interaction: desconto_callback(interaction, 0, button_sem_desconto,
                                                                         view_descontos)

    button_desconto_10 = Button(label="Desconto 10%", style=discord.ButtonStyle.success)
    button_desconto_10.callback = lambda interaction: desconto_callback(interaction, 10, button_desconto_10,
                                                                        view_descontos)

    button_desconto_20 = Button(label="Desconto 20%", style=discord.ButtonStyle.success)
    button_desconto_20.callback = lambda interaction: desconto_callback(interaction, 20, button_desconto_20,
                                                                        view_descontos)

    view_descontos.add_item(button_sem_desconto)
    view_descontos.add_item(button_desconto_10)
    view_descontos.add_item(button_desconto_20)

    # Botão para finalizar
    view_finalizar = View()
    button_finalizar = Button(label="Finalizar", style=discord.ButtonStyle.danger)
    button_finalizar.callback = finalizar_callback
    view_finalizar.add_item(button_finalizar)

    # Enviando as views separadas para o canal específico do servidor e armazenando as mensagens
    msg1 = await channel.send("Escolha as opções de tunagem de motos:", view=view_motos)
    msg2 = await channel.send("Escolha as opções de tunagem de carros:", view=view_carros)

    # Salvando as mensagens para poder deletar depois
    user_messages[user.id].append(msg1)
    user_messages[user.id].append(msg2)

    # Enviando cada view de modificações e salvando as mensagens
    for i, view in enumerate(views_modificacoes):
        msg = await channel.send(f"Escolha as modificações ({i + 1}/{len(views_modificacoes)}):", view=view)
        user_messages[user.id].append(msg)

    # Enviando opções de descontos e salvando a mensagem
    msg3 = await channel.send("Escolha um desconto:", view=view_descontos)
    user_messages[user.id].append(msg3)

    # Enviando o botão de finalizar e salvando a mensagem
    msg4 = await channel.send("Quando terminar, clique em finalizar:", view=view_finalizar)
    user_messages[user.id].append(msg4)


# Evento para quando um novo usuário envia uma mensagem no canal
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.id == SERVER_CHANNEL_ID:
        if message.author.id not in user_sessions:
            user_sessions[message.author.id] = 0
            user_discount[message.author.id] = 0  # Reseta o desconto também
            await start_user_session(message.author, message.channel)


# Inicie o bot com o token
bot.run('Your Bot token here')
