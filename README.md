# usar esse comando do commit pra saber quem e quando foi feita a alteração
```bash
git branch
git status
git add .
git commit -m "Jose leonam $(Get-Date)"
```
```bash
git push
```
ignora erro de commits do github
```bash
git push origin main --force
```
apaga codigo local e atualiza com o git
```bash
git fetch origin
git reset --hard origin/<nome da branch>
```