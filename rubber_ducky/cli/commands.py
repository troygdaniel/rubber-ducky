"""CLI commands for rubber-ducky using Click."""

import click
from rich.console import Console
from rich.panel import Panel
from pathlib import Path
import sys

from rubber_ducky.config import settings

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Rubber Ducky - Local voice conversation system.

    Privacy-focused voice assistant with WhisperX transcription,
    Coqui XTTS v2 voice cloning, and configurable LLMs.
    """
    pass


@cli.command()
@click.option('--provider', type=click.Choice(['claude', 'ollama']), help='LLM provider to use')
@click.option('--voice', type=click.Path(exists=True), help='Voice sample to use')
@click.option('--debug', is_flag=True, help='Enable debug output')
def converse(provider, voice, debug):
    """Start a voice conversation.

    Example:
        rubber-ducky converse
        rubber-ducky converse --provider ollama
        rubber-ducky converse --voice ~/my-voice.wav
    """
    try:
        # Override settings if provided
        if provider:
            settings.llm_provider = provider
        if voice:
            settings.xtts_voice_sample = voice

        # Check prerequisites
        if settings.llm_provider == "claude" and not settings.claude_api_key:
            console.print("[red]Error: Claude API key not configured.[/red]")
            console.print("Set RUBBER_DUCKY_CLAUDE_API_KEY in .env file")
            sys.exit(1)

        if not settings.xtts_voice_sample:
            console.print("[yellow]Warning: No voice sample configured. Using default XTTS voice.[/yellow]")
            console.print("Run 'rubber-ducky clone-voice' to create a custom voice.")

        console.print(Panel.fit(
            "[bold cyan]Rubber Ducky - Voice Conversation[/bold cyan]\n\n"
            f"LLM: {settings.llm_provider} ({settings.claude_model if settings.llm_provider == 'claude' else settings.ollama_model})\n"
            f"Voice: {settings.xtts_voice_sample or 'default'}\n"
            f"Debug: {debug}",
            title="Configuration"
        ))

        # Import here to avoid loading models during other commands
        from rubber_ducky.conversation.engine import ConversationEngine

        engine = ConversationEngine(settings, debug=debug)
        engine.start()

    except KeyboardInterrupt:
        console.print("\n[yellow]Conversation ended by user.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
def setup():
    """Initial setup: check dependencies and download models.

    This command:
    - Checks for CUDA availability
    - Downloads WhisperX models
    - Downloads XTTS v2 models
    - Tests audio devices
    """
    console.print(Panel.fit(
        "[bold cyan]Rubber Ducky Setup[/bold cyan]",
        title="Setup Wizard"
    ))

    try:
        # Check Python version
        import sys
        py_version = sys.version_info
        console.print(f"✓ Python {py_version.major}.{py_version.minor}.{py_version.micro}")

        if py_version < (3, 10) or py_version >= (3, 15):
            console.print("[red]✗ Python 3.10-3.14 required[/red]")
            sys.exit(1)

        # Check PyTorch
        try:
            import torch
            console.print(f"✓ PyTorch {torch.__version__}")
            if torch.cuda.is_available():
                console.print(f"✓ CUDA available (GPU: {torch.cuda.get_device_name(0)})")
            else:
                console.print("[yellow]! CUDA not available (will use CPU - slower)[/yellow]")
        except ImportError:
            console.print("[red]✗ PyTorch not installed[/red]")
            console.print("Install: pip install torch torchvision torchaudio")
            sys.exit(1)

        # Check WhisperX
        try:
            import whisperx
            console.print("✓ WhisperX installed")
        except ImportError:
            console.print("[red]✗ WhisperX not installed[/red]")
            console.print("Install: pip install whisperx")
            sys.exit(1)

        # Check Coqui TTS
        try:
            import TTS
            console.print("✓ Coqui TTS installed")
        except ImportError:
            console.print("[red]✗ Coqui TTS not installed[/red]")
            console.print("Install: pip install coqui-tts")
            sys.exit(1)

        # Check audio devices
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            console.print("\n[bold]Audio Devices:[/bold]")

            input_devices = [d for i, d in enumerate(devices) if d['max_input_channels'] > 0]
            output_devices = [d for i, d in enumerate(devices) if d['max_output_channels'] > 0]

            if input_devices:
                console.print(f"  Microphones: {len(input_devices)} found")
                for i, d in enumerate(input_devices[:3]):
                    console.print(f"    [{i}] {d['name']}")
            else:
                console.print("[red]  ✗ No microphones found[/red]")

            if output_devices:
                console.print(f"  Speakers: {len(output_devices)} found")
                for i, d in enumerate(output_devices[:3]):
                    console.print(f"    [{i}] {d['name']}")
            else:
                console.print("[red]  ✗ No speakers found[/red]")

        except Exception as e:
            console.print(f"[yellow]! Audio device check failed: {e}[/yellow]")

        # Download models
        console.print("\n[bold]Downloading models...[/bold]")
        console.print("[yellow]Note: First run will download ~2.3 GB of models[/yellow]")

        # TODO: Download WhisperX model
        console.print(f"→ WhisperX '{settings.whisper_model}' model will download on first use")

        # TODO: Download XTTS v2 model
        console.print("→ XTTS v2 model will download on first use")

        console.print("\n[green]✓ Setup complete![/green]")
        console.print("\nNext steps:")
        console.print("  1. Clone your voice (optional): rubber-ducky clone-voice --sample voice.wav --name Troy")
        console.print("  2. Configure LLM: edit .env with CLAUDE_API_KEY or start Ollama")
        console.print("  3. Start conversation: rubber-ducky converse")

    except Exception as e:
        console.print(f"[red]Setup failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--sample', required=True, type=click.Path(exists=True), help='Audio file with voice sample (6-10 seconds recommended)')
@click.option('--name', required=True, help='Name for this voice sample')
def clone_voice(sample, name):
    """Clone a voice from an audio sample.

    Provide a 6-10 second audio sample of clear speech
    to create a custom voice for TTS.

    Example:
        rubber-ducky clone-voice --sample ~/voice.wav --name Troy
    """
    try:
        console.print(Panel.fit(
            "[bold cyan]Voice Cloning[/bold cyan]",
            title="XTTS v2"
        ))

        sample_path = Path(sample).expanduser()
        console.print(f"Sample: {sample_path}")

        # TODO: Implement voice cloning
        # 1. Load audio sample
        # 2. Validate duration (6-10 seconds ideal)
        # 3. Test with XTTS
        # 4. Save to voice_samples/
        # 5. Update config

        console.print("[yellow]Voice cloning not yet implemented[/yellow]")
        console.print("This will be implemented in Phase 4 of development")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
def devices():
    """List available audio devices.

    Shows all microphones and speakers detected on the system.
    """
    try:
        import sounddevice as sd

        console.print(Panel.fit(
            "[bold cyan]Audio Devices[/bold cyan]",
            title="Available Devices"
        ))

        devices = sd.query_devices()

        console.print("\n[bold]Input Devices (Microphones):[/bold]")
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                default = " [default]" if i == sd.default.device[0] else ""
                console.print(f"  [{i}] {device['name']}{default}")

        console.print("\n[bold]Output Devices (Speakers):[/bold]")
        for i, device in enumerate(devices):
            if device['max_output_channels'] > 0:
                default = " [default]" if i == sd.default.device[1] else ""
                console.print(f"  [{i}] {device['name']}{default}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--key', help='Config key to view/update')
@click.option('--value', help='Value to set (requires --key)')
def config(key, value):
    """View or update configuration.

    Example:
        rubber-ducky config
        rubber-ducky config --key llm_provider
        rubber-ducky config --key llm_provider --value ollama
    """
    try:
        if key is None:
            # Show all config
            console.print(Panel.fit(
                "[bold cyan]Rubber Ducky Configuration[/bold cyan]",
                title="Current Settings"
            ))

            console.print("\n[bold]Paths:[/bold]")
            console.print(f"  data_dir: {settings.data_dir}")
            console.print(f"  voice_samples_dir: {settings.voice_samples_dir}")
            console.print(f"  database_path: {settings.database_path}")

            console.print("\n[bold]LLM:[/bold]")
            console.print(f"  llm_provider: {settings.llm_provider}")
            console.print(f"  claude_model: {settings.claude_model}")
            console.print(f"  ollama_model: {settings.ollama_model}")

            console.print("\n[bold]Audio:[/bold]")
            console.print(f"  sample_rate: {settings.sample_rate}")
            console.print(f"  whisper_model: {settings.whisper_model}")

            console.print("\n[bold]Voice:[/bold]")
            console.print(f"  xtts_voice_sample: {settings.xtts_voice_sample or 'default'}")

        elif value is None:
            # Show single key
            if hasattr(settings, key):
                console.print(f"{key}: {getattr(settings, key)}")
            else:
                console.print(f"[red]Unknown config key: {key}[/red]")
                sys.exit(1)
        else:
            # Update key
            console.print("[yellow]Config updates not yet implemented[/yellow]")
            console.print("Edit .env or config.yaml to change settings")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
