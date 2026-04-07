# Sistema de Denúncias
  usar esse comando do commit pra saber quem e quando foi feita a alteração

git branch
git status
git add .
git commit -m "Seu nome $(Get-Date)" windows
git commit -m "Seu nome $(date)" linux
git push
git pull

# apaga codigo local e atualiza com o git

git fetch origin
git reset --hard origin/main
