# mlparams
minimalist hyperparam configuration files stored as YAML

## usage

```python
from dataclasses import dataclass

from mlparams import from_yaml, to_yaml


@dataclass(frozen=True)
class SomeOtherConfiguration:
  dtype: str
  shape: tuple[int, ...]

@dataclass(frozen=True)
class SomeConfiguration:
  foo: str
  bar: dict[str, int]
  subconfig: SomeOtherConfiguration
  
  
config = SomeConfiguration(
  foo="foo",
  bar={
    "asdf": 5
  },
  subconfig=SomeOtherConfiguration(
    dtype="float32",
    shape=(2, 3, 4)
  )
)
  
# store to YAML file
with open("myconfig.yaml", "w") as f:
  to_yaml(config, f)
  
  
# load from YAML file with correct type info
with open("myconfig.yaml", "r") as f:
  config = from_yaml(SomeConfiguration, f)
  ```

Will create / parse the following YAML config file

```yaml
foo: "foo"
bar:
  asdf: 5
subconfig:
  dtype: "float32"
  shape: [2, 3, 4]
```
