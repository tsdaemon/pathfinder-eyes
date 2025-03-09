include .env

sync:
	rsync -av --exclude-from .rsync-exclude $(RSYNC_ARGS) . $(SSH_USER)@$(SSH_HOST):/home/$(SSH_USER)/eyes

syncr:
	rsync -av --exclude-from .rsync-exclude $(RSYNC_ARGS) $(SSH_USER)@$(SSH_HOST):/home/$(SSH_USER)/eyes/. .
