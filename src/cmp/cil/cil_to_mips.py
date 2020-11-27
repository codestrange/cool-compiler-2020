from typing import Dict, List

from .ast import (
    AllocateNode,
    ArgNode,
    ArithmeticNode,
    AssignNode,
    CleanArgsNode,
    ComplementNode,
    ConcatNode,
    CopyNode,
    DataNode,
    DivNode,
    DynamicCallNode,
    EqualNode,
    ErrorNode,
    FunctionNode,
    GetAttribNode,
    GotoIfNode,
    GotoNode,
    IsVoidNode,
    LabelNode,
    LengthNode,
    LessEqNode,
    LessNode,
    LocalNode,
    MinusNode,
    ParamNode,
    PlusNode,
    PrintIntNode,
    PrintStrNode,
    ProgramNode,
    ReadIntNode,
    ReadStrNode,
    ReturnNode,
    SetAttribNode,
    StarNode,
    StaticCallNode,
    StringEqualNode,
    SubstringNode,
    TypeNameNode,
    TypeNode,
    TypeOfNode,
)
from .utils import TypeData, on, when
from .utils.mips_syntax import Mips
from .utils.mips_syntax import Register as Reg


class CIL_TO_MIPS(object):
    def __init__(self, data_size: int = 8):
        self.types = []
        self.types_offsets: Dict[str, TypeData] = dict()
        self.local_vars_offsets = dict()
        self.actual_args = dict()
        self.mips = Mips()
        self.data_size = data_size
        self.label_count = -1
        self.registers_to_save: List[Reg] = [Reg.ra]

    def build_types_data(self, types):
        for idx, typex in enumerate(types):
            self.types_offsets[typex.name] = TypeData(idx, typex)

    def get_label(self):
        self.label_count += 1
        return f"mip_label_{self.label_count}"

    def load_memory(self, dst: Reg, arg: str):
        if arg in self.actual_args or arg in self.local_vars_offsets:
            offset = (
                self.actual_args[arg] + 1
                if arg in self.actual_args
                else -self.local_vars_offsets[arg]
            ) * self.data_size

            self.mips.load_memory(dst, self.mips.offset(Reg.fp, offset))
        else:
            raise Exception(f"load_memory: The direction {arg} isn't an address")
        self.mips.empty()

    def store_memory(self, dst: Reg, arg: str):
        if arg in self.local_vars_offsets:
            offset = -self.local_vars_offsets[arg] * self.data_size
            self.mips.store_memory(dst, self.mips.offset(Reg.fp, offset))
        else:
            raise Exception(f"store_memory: The direction {arg} isn't an address")
        self.mips.empty()

    def load_arithmetic(self, node: ArithmeticNode):
        self.load_memory(Reg.t0, node.left)
        self.load_memory(Reg.t1, node.right)

    def store_registers(self):
        for reg in self.registers_to_save:
            self.mips.push(reg)

    def load_registers(self):
        for reg in reversed(self.registers_to_save):
            self.mips.pop(reg)

    @on("node")
    def visit(self, node):
        pass

    @when(ProgramNode)
    def visit(self, node: ProgramNode):  # noqa: F811
        self.types = node.dottypes
        self.build_types_data(self.types)

        for datanode in node.dotdata:
            self.visit(datanode)

        self.mips.label("main")

        self.mips.jal("entry")

        self.mips.exit()

        for function in node.dotcode:
            self.visit(function)

        self.mips.empty()

    @when(DataNode)
    def visit(self, node: DataNode):  # noqa: F811
        self.mips.data_label(node.name)
        self.mips.asciiz(node.value)

    @when(TypeNode)
    def visit(self, node: TypeNode):  # noqa: F811
        pass

    @when(FunctionNode)
    def visit(self, node: FunctionNode):  # noqa: F811
        self.mips.empty()
        self.mips.label(node.name)

        self.mips.comment("Set stack frame")
        self.mips.push(Reg.fp)
        self.mips.move(Reg.fp, Reg.sp)

        self.actual_args = dict()

        for idx, param in enumerate(node.params):
            self.visit(param, index=idx)

        self.mips.empty()
        self.mips.comment("Allocate memory for Local variables")
        for idx, local in enumerate(node.localvars):
            self.visit(local, index=idx)

        self.mips.empty()
        self.store_registers()
        self.mips.empty()
        self.mips.comment("Generating body code")
        for instruction in node.instructions:
            self.visit(instruction)

        self.actual_args = None
        self.mips.empty()
        self.load_registers()

        self.mips.comment("Clean stack variable space")
        self.mips.addi(
            Reg.sp,
            Reg.sp,
            len(node.localvars) * self.data_size,
        )
        self.mips.comment("Return")
        self.mips.pop(Reg.fp)
        self.mips.jr(Reg.ra)
        self.mips.empty()

    @when(ParamNode)
    def visit(self, node: ParamNode, index=0):  # noqa: F811
        self.actual_args[node.name] = index

    @when(LocalNode)
    def visit(self, node: LocalNode, index=0):  # noqa: F811
        self.mips.push(Reg.zero)
        assert node.name not in self.local_vars_offsets, f"Impossible {node.name}..."
        self.local_vars_offsets[node.name] = index

    @when(CopyNode)
    def visit(self, node: CopyNode):  # noqa: F811
        # TODO: Implement visitor
        pass

    @when(TypeNameNode)
    def visit(self, node: TypeNameNode):  # noqa: F811
        self.mips.comment("TypeNameNode")
        self.load_memory(Reg.t0, node.type)
        self.mips.load_memory(Reg.t1, self.mips.offset(Reg.t0, self.data_size))
        self.store_memory(Reg.t1, node.dest)
        self.mips.empty()

    @when(ErrorNode)
    def visit(self, node: ErrorNode):  # noqa: F811
        self.mips.comment("ErrorNode")
        self.mips.li(Reg.a0, 1)
        self.mips.exit2()
        self.mips.empty()

    @when(AssignNode)
    def visit(self, node: AssignNode):  # noqa: F811
        self.mips.comment("AssignNode")
        self.load_memory(Reg.t0, node.source)
        self.store_memory(Reg.t0, node.dest)
        self.mips.empty()

    @when(IsVoidNode)
    def visit(self, node: IsVoidNode):  # noqa: F811
        self.mips.comment("IsVoidNode")
        self.load_memory(Reg.t0, node.body)

        label = self.get_label()

        self.mips.li(Reg.t1, 0)
        self.mips.bne(Reg.t0, Reg.t1, label)
        self.mips.li(Reg.t1, 1)
        self.mips.label(label)
        self.store_memory(Reg.t1, node.dest)

        self.mips.empty()

    @when(ComplementNode)
    def visit(self, node: ComplementNode):  # noqa: F811
        self.mips.comment("ComplementNode")

        self.load_memory(Reg.t0, node.body)
        self.mips.nor(Reg.t1, Reg.t0, Reg.t0)
        self.store_memory(Reg.t1, node.dest)

        self.mips.empty()

    @when(LessNode)
    def visit(self, node: LessNode):  # noqa: F811
        self.load_arithmetic(node)
        self.mips.slt(Reg.t2, Reg.t0, Reg.t1)
        self.store_memory(Reg.t2, node.dest)
        self.mips.empty()

    @when(EqualNode)
    def visit(self, node: EqualNode):  # noqa: F811
        """
        ((a < b) + (b < a)) < 1  -> ==
        """
        self.load_arithmetic(node)
        self.mips.slt(Reg.t2, Reg.t0, Reg.t1)
        self.mips.slt(Reg.t3, Reg.t1, Reg.t0)

        self.mips.add(Reg.t0, Reg.t2, Reg.t3)
        self.mips.slti(Reg.t1, Reg.t0, 1)

        self.store_memory(Reg.t1, node.dest)
        self.mips.empty()

    @when(LessEqNode)
    def visit(self, node: LessEqNode):  # noqa: F811
        """
        a <= b -> ! b < a -> 1 - (b < a)
        """
        self.load_arithmetic(node)
        self.mips.slt(Reg.t2, Reg.t1, Reg.t0)
        self.mips.li(Reg.t3, 1)
        self.mips.sub(Reg.t0, Reg.t3, Reg.t2)
        self.store_memory(Reg.t0, node.dest)
        self.mips.empty()

    @when(PlusNode)
    def visit(self, node: PlusNode):  # noqa: F811
        self.load_arithmetic(node)
        self.mips.add(Reg.t2, Reg.t0, Reg.t1)
        self.store_memory(Reg.t2, node.dest)
        self.mips.empty()

    @when(MinusNode)
    def visit(self, node: MinusNode):  # noqa: F811
        self.load_arithmetic(node)
        self.mips.sub(Reg.t2, Reg.t0, Reg.t1)
        self.store_memory(Reg.t2, node.dest)
        self.mips.empty()

    @when(StarNode)
    def visit(self, node: StarNode):  # noqa: F811
        self.load_arithmetic(node)
        self.mips.mult(Reg.t2, Reg.t0, Reg.t1)
        self.mips.mflo(Reg.t0)
        self.store_memory(Reg.t0, node.dest)
        self.mips.empty()

    @when(DivNode)
    def visit(self, node: DivNode):  # noqa: F811
        self.load_arithmetic(node)
        self.mips.div(Reg.t2, Reg.t0, Reg.t1)
        self.mips.mflo(Reg.t0)
        self.store_memory(Reg.t0, node.dest)
        self.mips.empty()

    @when(AllocateNode)
    def visit(self, node: AllocateNode):  # noqa: F811
        self.mips.comment(f"AllocateNode: dest: {node.dest}, type: {node.type}")

        type_data = self.types_offsets[node.type]

        self.mips.comment(str(type_data))

        length = len(type_data.attr_offsets) + len(type_data.func_offsets) + 2
        length *= self.data_size
        self.mips.li(Reg.a0, length)
        self.mips.sbrk()
        self.store_memory(Reg.v0, node.dest)

        self.mips.li(Reg.t0, type_data.type)
        self.mips.store_memory(Reg.t0, self.mips.offset(Reg.v0))

        self.mips.la(Reg.t0, type_data.str)
        self.mips.store_memory(Reg.t0, self.mips.offset(Reg.v0, 1 * self.data_size))

        for offset in type_data.attr_offsets.values():
            self.mips.store_memory(
                Reg.zero,
                self.mips.offset(
                    Reg.v0,
                    offset * self.data_size,
                ),
            )

        for name, offset in type_data.func_offsets.items():
            direct_name = type_data.func_names[name]
            self.mips.la(Reg.t0, direct_name)
            self.mips.store_memory(
                Reg.t0,
                self.mips.offset(
                    Reg.v0,
                    offset * self.data_size,
                ),
            )

        self.mips.empty()

    @when(TypeOfNode)
    def visit(self, node: TypeOfNode):  # noqa: F811
        self.mips.comment("TypeOfNode")
        self.mips.la(Reg.t0, node.obj)
        self.load_memory(Reg.t1, self.mips.offset(Reg.t0))
        self.store_memory(Reg.t1, node.dest)
        self.mips.empty()

    @when(StaticCallNode)
    def visit(self, node: StaticCallNode):  # noqa: F811
        self.mips.comment("StaticCallNode")
        self.mips.jal(node.function)
        self.mips.empty()

    @when(DynamicCallNode)
    def visit(self, node: DynamicCallNode):  # noqa: F811
        self.mips.comment("DynamicCallNode")
        type_data = self.types_offsets[node.type]
        offset = type_data.func_offsets[node.method]
        self.load_memory(Reg.t0, node.obj)
        self.mips.load_memory(Reg.t1, self.mips.offset(Reg.t0, offset))
        self.mips.jal(self.mips.offset(Reg.t1))
        self.mips.empty()

    @when(ArgNode)
    def visit(self, node: ArgNode):  # noqa: F811
        self.mips.comment("ArgNode")
        self.load_memory(Reg.t0, node.name)
        self.mips.push(Reg.t0)
        self.mips.empty()

    @when(CleanArgsNode)
    def visit(self, node: CleanArgsNode):  # noqa: F811
        self.mips.comment("CleanArgsNode")
        self.mips.addi(
            Reg.sp,
            Reg.sp,
            node.nargs * self.data_size,
        )
        self.mips.empty()

    @when(ReturnNode)
    def visit(self, node: ReturnNode):  # noqa: F811
        self.mips.comment("ReturnNode")
        self.load_memory(Reg.v0, node.value)
        self.mips.empty()

    @when(ReadIntNode)
    def visit(self, node: ReadIntNode):  # noqa: F811
        self.mips.comment("ReadIntNode")
        self.load_memory(Reg.a0, node.dest)
        self.mips.read_int()
        self.mips.empty()

    @when(ReadStrNode)
    def visit(self, node: ReadStrNode):  # noqa: F811
        self.mips.comment("ReadStrNode")
        self.load_memory(Reg.a0, node.dest)
        self.mips.read_string()
        self.mips.empty()

    @when(PrintIntNode)
    def visit(self, node: PrintIntNode):  # noqa: F811
        self.mips.comment("PrintIntNode")
        self.load_memory(Reg.a0, node.str_addr)
        self.mips.print_int()
        self.mips.empty()

    @when(PrintStrNode)
    def visit(self, node: PrintStrNode):  # noqa: F811
        self.mips.comment("PrintStrNode")
        self.load_memory(Reg.a0, node.str_addr)
        self.mips.print_string()
        self.mips.empty()

    @when(LengthNode)
    def visit(self, node: LengthNode):  # noqa: F811
        # TODO: Implement visitor
        pass

    @when(ConcatNode)
    def visit(self, node: ConcatNode):  # noqa: F811
        # TODO: Implement visitor
        pass

    @when(SubstringNode)
    def visit(self, node: SubstringNode):  # noqa: F811
        # TODO: Implement visitor
        pass

    @when(StringEqualNode)
    def visit(self, node: StringEqualNode):  # noqa: F811
        # TODO: Implement visitor
        pass

    @when(GetAttribNode)
    def visit(self, node: GetAttribNode):  # noqa: F811
        self.mips.comment("GetAttribNode")
        self.load_memory(Reg.t0, node.obj)
        type_data = self.types_offsets[node.type]
        offset = type_data.attr_offsets[node.attrib]
        self.mips.load_memory(Reg.t1, self.mips.offset(Reg.t0, offset))
        self.store_memory(Reg.t1, node.dest)
        self.mips.empty()

    @when(SetAttribNode)
    def visit(self, node: SetAttribNode):  # noqa: F811
        self.mips.comment("SetAttribNode")
        self.load_memory(Reg.t0, node.obj)
        type_data = self.types_offsets[node.type]
        offset = type_data.attr_offsets[node.attrib]
        if node.value in self.local_vars_offsets:
            self.mips.comment(f"Seting local var {node.value}")
            self.load_memory(Reg.t1, node.value)
        else:
            try:
                value = int(node.value)
                high = value >> 16
                self.mips.comment(f"Seting literal int {node.value}")
                self.mips.li(Reg.t2, high)
                self.mips.li(Reg.t3, value)
                self.mips.sll(Reg.t4, Reg.t2, 16)
                self.mips.orr(Reg.t1, Reg.t3, Reg.t4)
            except ValueError:
                self.mips.comment(f"Seting data {node.value}")
                self.mips.la(Reg.t1, node.value)
        self.mips.store_memory(Reg.t1, self.mips.offset(Reg.t0, offset*self.data_size))
        self.mips.empty()

    @when(LabelNode)
    def visit(self, node: LabelNode):  # noqa: F811
        self.mips.comment("LabelNode")
        self.mips.label(node.label)
        self.mips.empty()

    @when(GotoNode)
    def visit(self, node: GotoNode):  # noqa: F811
        self.mips.comment("GotoNode")
        self.mips.j(node.label)
        self.mips.empty()

    @when(GotoIfNode)
    def visit(self, node: GotoIfNode):  # noqa: F811: F811
        self.mips.comment("GotoIfNode")
        self.load_memory(Reg.t0, node.value)
        self.mips.li(Reg.t1, 0)
        self.mips.bne(Reg.t0, Reg.t1, node.label)
        self.mips.empty()
