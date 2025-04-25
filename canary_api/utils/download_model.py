import logging
from pathlib import Path
from huggingface_hub import snapshot_download

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def download_model(model_name: str, local_dir: str = "./models") -> str:
    """
    Downloads the full model repository from Hugging Face Hub to a local directory.

    Args:
        model_name (str): Hugging Face model ID.
        local_dir (str): Directory to store the model.

    Returns:
        str: Path to the downloaded model.
    """
    target_dir = Path(local_dir) / model_name

    if target_dir.exists():
        print(f"Model already exists: {target_dir}")
        return str(target_dir)

    # Perform the snapshot download
    logger.info(f"Downloading '{model_name}' to '{target_dir}' via huggingface_hub...")
    snapshot_download(
        repo_id=model_name,
        local_dir=target_dir,
        force_download=False
    )

    logger.info(f"Model downloaded to: {target_dir}")
    return str(target_dir)


if __name__ == "__main__":
    import fire

    fire.Fire(download_model)
