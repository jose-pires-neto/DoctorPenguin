# Doctor Penguin 🐧💻

**Doctor Penguin** é um "Desktop Pet" inteligente e interativo para Windows. Ele fica passeando pela sua tela em segundo plano e atua como seu companheiro e assistente pessoal de sistema!

Além de ser um pet fofo e ter vida própria (ele pesca e bota ovos no seu desktop!), se o seu PC estiver sofrendo (com a RAM nas alturas, lixeira cheia ou acumulando arquivos temporários), o Doctor Penguin vai aparecer, abrir um balão de fala animado estilo HQ e se oferecer para consertar o problema para você.

E mais: ele possui **integração nativa com Inteligência Artificial** (via Ollama) para conversar com você!

## ✨ Funcionalidades

- **Mascote de Mesa com Vida Própria:** O pinguim anda livremente por cima das suas janelas, com animações em 8 direções. Se ficar entediado, ele pode abrir um buraco de gelo no seu monitor para **pescar** sozinho ou botar **ovos** interativos.
- **Integração com I.A (Ollama):** Faça carinho ou clique no pinguim para interagir. Se o Ollama estiver rodando na sua máquina, o pinguim gerará diálogos dinâmicos baseados no que você está fazendo (ele sabe qual programa está aberto e reage ao contexto!).
- **Animações de UI Orgânicas:** O balão de diálogo possui efeitos vivos de flutuação e respiração. Quando ele está "pensando", uma nuvem animada autêntica aparece no estilo clássico de quadrinhos.
- **Monitoramento de RAM:** Detecta se a sua memória RAM ultrapassar o limite seguro e identifica qual processo está devorando mais memória.
- **Limpeza de Lixeira e Temporários:** Fica de olho no acúmulo de lixo. Se a lixeira passar dos limites ou a pasta `Temp` lotar, ele sugere uma faxina.
- **Ações Rápidas:** Botões diretamente no balão de fala permitem que você autorize a limpeza ou encerre processos pesados com um simples clique.

## 🚀 Como instalar e executar

Este projeto foi construído em Python. Você precisará do [Python 3.10+](https://www.python.org/downloads/) instalado no seu Windows.

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/jose-pires-neto/DoctorPenguin.git
   cd DoctorPenguin
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute o Doctor Penguin:**
   ```bash
   python main.py
   ```

## 📦 Como gerar o Executável (.exe)

O projeto inclui um script em PowerShell pronto para compilar todo o código Python em um único arquivo executável para o Windows! Isso significa que você poderá rodar o pinguim em outros computadores sem precisar instalar o Python ou as dependências.

1. Clique com o botão direito no arquivo `build.ps1` e selecione **Executar com o PowerShell** (ou rode `.\build.ps1` pelo seu terminal).
2. O script instalará o PyInstaller automaticamente e fará todo o processo de "Build" empacotando os assets.
3. Ao finalizar, você encontrará o seu `DoctorPenguin.exe` pronto para uso dentro da pasta recém-criada chamada `dist/`.

## 🛠️ Ferramentas Inclusas (Modificando o Pinguim)
Dentro da pasta `tools/`, você encontrará uma imagem bruta de sprites e um script chamado `sprite_configurator.py`.
Caso queira mudar as animações ou criar o seu próprio mascote personalizado:
1. Substitua os sprites originais.
2. Rode `python tools/sprite_configurator.py` para abrir uma interface visual. Nela, você pode "clicar e arrastar" cada quadro de animação (Andar, Ficar Parado, Sentar) para a posição correta.
3. Salve e substitua a imagem `penguin_sprites_aligned.png` na raiz do projeto.

## 📝 Licença

Este projeto está licenciado sob a **Licença MIT** - veja o arquivo [LICENSE](LICENSE) para mais detalhes. Sinta-se livre para usar, modificar e melhorar o Doctor Penguin!
