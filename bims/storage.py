from pipeline.storage import PipelineManifestStorage


class NoSourceMapsStorage(PipelineManifestStorage):
    def hashed_name(self, name, content=None, filename=None):
        try:
            return super().hashed_name(name, content=content, filename=filename)
        except ValueError:
            return name

