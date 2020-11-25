from .ast import (
    ProgramNode,
    TypeNode,
    FunctionNode,
    ParamNode,
    LocalNode,
    AssignNode,
    PlusNode,
    MinusNode,
    StarNode,
    DivNode,
    AllocateNode,
    TypeOfNode,
    StaticCallNode,
    DynamicCallNode,
    ArgNode,
    ReturnNode,
    ReadStrNode,
    ReadIntNode,
    PrintStrNode,
    PrintIntNode,
    LengthNode,
    ConcatNode,
    PrefixNode,
    SubstringNode,
    GetAttribNode,
    SetAttribNode,
    LabelNode,
    GotoNode,
    GotoIfNode,
    DataNode,
    LessNode,
    LessEqNode,
    ComplementNode,
    IsVoidNode,
    EqualNode,
    ConformNode,
    CleanArgsNode,
    ErrorNode,
    CopyNode,
    TypeNameNode,
    StringEqualNode,
)
from .utils import on, when
from .utils.mips_syntax import Mips, Register as Reg # noqa


class CIL_TO_MIPS(object):
    def __init__(self):
        self.types = []
        self.types_offsets = dict()
        self.local_vars_offsets = dict()
        self.actual_args = dict()
        self.mips = Mips()

    @on("node")
    def visit(self, node):
        pass

    @when(ProgramNode)
    def visit(self, node: ProgramNode): # noqa
        self.types = node.dottypes
        self.build_types_data(self.types)

        for datanode in node.dotdata:
            self.visit(datanode)

        self.mips.label("main")

        self.mips.jal("entry")

        self.mips.exit()

        for function in node.dotcode:
            self.visit(function)

    @when(DataNode)
    def visit(self, node: DataNode):  # noqa
        self.mips.write_data(f'{node.name}: .asciiz "{node.value}"')

    @when(TypeNode)
    def visit(self, node: TypeNode):  # noqa
        pass

    @when(FunctionNode)
    def visit(self, node: FunctionNode):  # noqa
        self.write_inst("")
        self.write_inst(f"{node.name}: ;")
        self.write_push("$fp")
        self.write_inst("add $fp, $0, $sp")
        self.actual_args = dict()

        self.write_inst("")
        for idx, param in enumerate(node.params):
            self.visit(param, index=idx)

        self.write_inst("")
        for idx, local in enumerate(node.localvars):
            self.visit(local, index=idx)

        self.write_inst("")
        # self.store_registers()
        self.write_inst("")
        for instruction in node.instructions:
            self.visit(instruction)

        self.actual_args = None
        self.write_inst("")
        # self.load_registers()

        for _ in node.localvars:
            self.write_inst("addi $sp, $sp, 8")
        self.write_pop("$fp")
        self.write_inst("jr $ra")
        self.write_inst("")

    @when(ParamNode)
    def visit(self, node: ParamNode, index=0):  # noqa
        self.actual_args[node.name] = index

    @when(LocalNode)
    def visit(self, node: LocalNode, index=0):  # noqa
        self.write_push("$zero")
        assert node.name not in self.local_vars_offsets, \
            f"Impossible {node.name}..."
        self.local_vars_offsets[node.name] = index

    @when(CopyNode)
    def visit(self, node: CopyNode):  # noqa
        pass

    @when(TypeNameNode)
    def visit(self, node: TypeNameNode):  # noqa
        pass

    @when(ErrorNode)
    def visit(self, node: ErrorNode):  # noqa
        pass

    @when(AssignNode)
    def visit(self, node: AssignNode):  # noqa
        pass

    @when(ConformNode)
    def visit(self, node: ConformNode):  # noqa
        pass

    @when(IsVoidNode)
    def visit(self, node: IsVoidNode):  # noqa
        pass

    @when(ComplementNode)
    def visit(self, node: ComplementNode):  # noqa
        pass

    @when(LessNode)
    def visit(self, node: LessNode):  # noqa
        pass

    @when(EqualNode)
    def visit(self, node: EqualNode):  # noqa
        pass

    @when(LessEqNode)
    def visit(self, node: LessEqNode):  # noqa
        pass

    @when(PlusNode)
    def visit(self, node: PlusNode):  # noqa
        pass

    @when(MinusNode)
    def visit(self, node: MinusNode):  # noqa
        pass

    @when(StarNode)
    def visit(self, node: StarNode):  # noqa
        pass

    @when(DivNode)
    def visit(self, node: DivNode):  # noqa
        pass

    @when(AllocateNode)
    def visit(self, node: AllocateNode):  # noqa
        pass

    @when(TypeOfNode)
    def visit(self, node: TypeOfNode):  # noqa
        pass

    @when(StaticCallNode)
    def visit(self, node: StaticCallNode):  # noqa
        pass

    @when(DynamicCallNode)
    def visit(self, node: DynamicCallNode):  # noqa
        pass

    @when(ArgNode)
    def visit(self, node: ArgNode):  # noqa
        pass

    @when(CleanArgsNode)
    def visit(self, node: CleanArgsNode):  # noqa
        pass

    @when(ReturnNode)
    def visit(self, node: ReturnNode):  # noqa
        pass

    @when(ReadIntNode)
    def visit(self, node: ReadIntNode):  # noqa
        pass

    @when(ReadStrNode)
    def visit(self, node: ReadStrNode):  # noqa
        pass

    @when(PrintIntNode)
    def visit(self, node: PrintIntNode):  # noqa
        pass

    @when(PrintStrNode)
    def visit(self, node: PrintStrNode):  # noqa
        pass

    @when(LengthNode)
    def visit(self, node: LengthNode):  # noqa
        pass

    @when(ConcatNode)
    def visit(self, node: ConcatNode):  # noqa
        pass

    @when(PrefixNode)
    def visit(self, node: PrefixNode):  # noqa
        pass

    @when(SubstringNode)
    def visit(self, node: SubstringNode):  # noqa
        pass

    @when(StringEqualNode)
    def visit(self, node: StringEqualNode):  # noqa
        pass

    @when(GetAttribNode)
    def visit(self, node: GetAttribNode):  # noqa
        pass

    @when(SetAttribNode)
    def visit(self, node: SetAttribNode):  # noqa
        pass

    @when(LabelNode)
    def visit(self, node: LabelNode):  # noqa
        pass

    @when(GotoNode)
    def visit(self, node: GotoNode):  # noqa
        pass

    @when(GotoIfNode)
    def visit(self, node: GotoIfNode):  # noqa
        pass
