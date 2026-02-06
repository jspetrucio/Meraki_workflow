# Homebrew Formula for CNL (Cisco Neural Language)
# To install: brew install cnl.rb
# Or via tap: brew tap cisco/cnl && brew install cnl

class Cnl < Formula
  include Language::Python::Virtualenv

  desc "Natural language interface for Meraki network management"
  homepage "https://github.com/jspetrucio/Meraki_workflow"
  url "https://files.pythonhosted.org/packages/source/c/cnl/cnl-0.1.0.tar.gz"
  sha256 "" # Will be filled when published to PyPI
  license "MIT"

  # Python 3.10+ required
  depends_on "python@3.12"

  # Core dependencies
  resource "meraki" do
    url "https://files.pythonhosted.org/packages/source/m/meraki/meraki-1.53.0.tar.gz"
    sha256 "" # Auto-populated by homebrew-pypi-poet
  end

  resource "python-dotenv" do
    url "https://files.pythonhosted.org/packages/source/p/python-dotenv/python_dotenv-1.0.0.tar.gz"
    sha256 "" # Auto-populated
  end

  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/source/p/pydantic/pydantic-2.0.0.tar.gz"
    sha256 "" # Auto-populated
  end

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/source/p/pyyaml/PyYAML-6.0.tar.gz"
    sha256 "" # Auto-populated
  end

  resource "cryptography" do
    url "https://files.pythonhosted.org/packages/source/c/cryptography/cryptography-42.0.0.tar.gz"
    sha256 "" # Auto-populated
  end

  resource "litellm" do
    url "https://files.pythonhosted.org/packages/source/l/litellm/litellm-1.50.0.tar.gz"
    sha256 "" # Auto-populated
  end

  resource "fastapi" do
    url "https://files.pythonhosted.org/packages/source/f/fastapi/fastapi-0.115.0.tar.gz"
    sha256 "" # Auto-populated
  end

  resource "uvicorn" do
    url "https://files.pythonhosted.org/packages/source/u/uvicorn/uvicorn-0.34.0.tar.gz"
    sha256 "" # Auto-populated
  end

  resource "httpx" do
    url "https://files.pythonhosted.org/packages/source/h/httpx/httpx-0.27.0.tar.gz"
    sha256 "" # Auto-populated
  end

  resource "click" do
    url "https://files.pythonhosted.org/packages/source/c/click/click-8.1.0.tar.gz"
    sha256 "" # Auto-populated
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/source/r/rich/rich-13.0.0.tar.gz"
    sha256 "" # Auto-populated
  end

  resource "jinja2" do
    url "https://files.pythonhosted.org/packages/source/j/jinja2/Jinja2-3.1.0.tar.gz"
    sha256 "" # Auto-populated
  end

  def install
    # Install all Python dependencies into virtualenv
    virtualenv_install_with_resources
  end

  test do
    # Test that the CLI command exists and shows version
    assert_match "cnl", shell_output("#{bin}/cnl --help")

    # Test Python import
    system libexec/"bin/python", "-c", "import scripts.cli"
  end
end
