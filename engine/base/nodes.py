from pydantic import Field, HttpUrl, model_validator
from typing import Literal, Union, Any

from .models import ModelWrapper, LLMParameters
from .common import BaseNode

class LLMNode(BaseNode):
    type: Literal["LLMNode"]
    model: ModelWrapper
    parameters: LLMParameters = Field(default_factory=LLMParameters)
    
    # This validator runs *before* field validation
    @model_validator(mode='before')
    @classmethod
    def extract_param_dict(cls, data: Any) -> Any:
        """
        Extracts 'model' and 'parameters' from 'param_dict' and
        places them at the top level of the input data.
        """
        if isinstance(data, dict):
            param_dict = data.get("param_dict")
            if param_dict and isinstance(param_dict, dict):
                processed_data = data.copy()
                if 'model' in param_dict:
                    processed_data['model'] = param_dict['model']
                if 'parameters' in param_dict:
                    processed_data['parameters'] = param_dict['parameters']
                if 'param_dict' in processed_data:
                    del processed_data['param_dict']
                return processed_data     
        return data

class StartNode(BaseNode):
    type: Literal["START"]

class EndNode(BaseNode):
    type: Literal["END"]

class ToolNode(BaseNode):
    type: Literal["ToolNode"]
    tool_endpoint: HttpUrl
    # This validator runs *before* field validation
    @model_validator(mode='before')
    @classmethod
    def extract_param_dict(cls, data: Any) -> Any:
        """
        Extracts 'model' and 'parameters' from 'param_dict' and
        places them at the top level of the input data.
        """
        if isinstance(data, dict):
            param_dict = data.get("param_dict")
            if param_dict and isinstance(param_dict, dict):
                processed_data = data.copy()
                if 'tool_endpoint' in param_dict:
                    processed_data['tool_endpoint'] = param_dict['tool_endpoint']
                if 'param_dict' in processed_data:
                    del processed_data['param_dict']
                return processed_data          
        return data

class A2ANode(BaseNode):
    type: Literal["A2ANode"]
    api_base_url: HttpUrl
    # This validator runs *before* field validation
    @model_validator(mode='before')
    @classmethod
    def extract_param_dict(cls, data: Any) -> Any:
        """
        Extracts 'api_base_url' from 'param_dict' and
        places it at the top level of the input data.
        """
        if isinstance(data, dict):
            param_dict = data.get("param_dict")
            if param_dict and isinstance(param_dict, dict):
                processed_data = data.copy()
                if 'api_base_url' in param_dict:
                    processed_data['api_base_url'] = param_dict['api_base_url']
                if 'param_dict' in processed_data:
                    del processed_data['param_dict']
                return processed_data          
        return data

AnyNode = Union[StartNode, EndNode, LLMNode, ToolNode, A2ANode]
