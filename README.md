# Doctor Penguin 🐧💻

**Doctor Penguin** é um "Desktop Pet" inteligente e interativo para Windows. Ele fica passeando pela sua tela em segundo plano e, como um bom médico de sistema, monitora constantemente a saúde do seu computador!

Se o seu PC estiver sofrendo (com a RAM nas alturas, lixeira cheia ou acumulando arquivos temporários), o Doctor Penguin vai aparecer, bater na sua tela com um balãozinho de fala estilo HQ (Histórias em Quadrinhos) e se oferecer para consertar o problema para você.

## ✨ Funcionalidades

- **Mascote de Mesa (Desktop Pet):** O pinguim anda livremente por cima das suas janelas do Windows, com animações em 8 direções diferentes.
- **Monitoramento de RAM:** Detecta se a sua memória RAM ultrapassar o limite seguro (padrão de 75%) e identifica qual processo está devorando mais memória.
- **Limpeza de Lixeira:** Fica de olho no acúmulo de lixo. Se a lixeira passar de 500MB ou 50 itens, ele sugere esvaziá-la.
- **Arquivos Temporários:** Monitora a pasta `Temp` do Windows e avisa se você pode liberar espaço em disco apagando lixo oculto.
- **Interface HQ Interativa:** O pinguim conversa com você usando um balão de diálogo retro e super amigável, com direito a efeitos sonoros!
- **Ações Rápidas:** Botões diretamente no balão de fala permitem que você autorize a limpeza ou encerre processos pesados com um simples clique.

## 🚀 Como instalar e executar

Este projeto foi construído em Python. Você precisará do [Python 3.10+](https://www.python.org/downloads/) instalado no seu Windows.

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/jose-pires-neto/DoctorPenguin.git
   cd DoctorPenguin
   ```

2. **Instale as dependências:**
   O Doctor Penguin utiliza o `pygame` para desenhar na tela e bibliotecas como `psutil` e `pywin32` para monitorar o Windows.
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute o Doctor Penguin:**
   ```bash
   python main.py
   ```

## 🛠️ Ferramentas Inclusas (Modificando o Pinguim)
Dentro da pasta `tools/`, você encontrará uma imagem bruta de sprites e um script chamado `sprite_configurator.py`.
Caso queira mudar as animações ou criar o seu próprio mascote personalizado:
1. Substitua os sprites.
2. Rode `python tools/sprite_configurator.py` para abrir uma interface visual onde você pode "clicar e arrastar" cada quadro de animação (Andar, Ficar Parado, Sentar) para a posição correta (Norte, Sul, Leste, Oeste, etc).
3. Salve e substitua a imagem `penguin_sprites_aligned.png` na raiz do projeto.

## 📝 Licença

Este projeto está licenciado sob a **Licença MIT** - veja o arquivo [LICENSE](LICENSE) para mais detalhes. Sinta-se livre para usar, modificar e melhorar o Doctor Penguin!
