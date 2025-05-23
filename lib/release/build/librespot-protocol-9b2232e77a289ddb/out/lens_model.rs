// This file is generated by rust-protobuf 3.7.1. Do not edit
// .proto file is parsed by pure
// @generated

// https://github.com/rust-lang/rust-clippy/issues/702
#![allow(unknown_lints)]
#![allow(clippy::all)]

#![allow(unused_attributes)]
#![cfg_attr(rustfmt, rustfmt::skip)]

#![allow(dead_code)]
#![allow(missing_docs)]
#![allow(non_camel_case_types)]
#![allow(non_snake_case)]
#![allow(non_upper_case_globals)]
#![allow(trivial_casts)]
#![allow(unused_results)]
#![allow(unused_mut)]

//! Generated file from `lens-model.proto`

/// Generated files are compatible only with the same version
/// of protobuf runtime.
const _PROTOBUF_VERSION_CHECK: () = ::protobuf::VERSION_3_7_1;

// @@protoc_insertion_point(message:spotify.lens.model.proto.Lens)
#[derive(PartialEq,Clone,Default,Debug)]
pub struct Lens {
    // message fields
    // @@protoc_insertion_point(field:spotify.lens.model.proto.Lens.identifier)
    pub identifier: ::std::string::String,
    // special fields
    // @@protoc_insertion_point(special_field:spotify.lens.model.proto.Lens.special_fields)
    pub special_fields: ::protobuf::SpecialFields,
}

impl<'a> ::std::default::Default for &'a Lens {
    fn default() -> &'a Lens {
        <Lens as ::protobuf::Message>::default_instance()
    }
}

impl Lens {
    pub fn new() -> Lens {
        ::std::default::Default::default()
    }

    fn generated_message_descriptor_data() -> ::protobuf::reflect::GeneratedMessageDescriptorData {
        let mut fields = ::std::vec::Vec::with_capacity(1);
        let mut oneofs = ::std::vec::Vec::with_capacity(0);
        fields.push(::protobuf::reflect::rt::v2::make_simpler_field_accessor::<_, _>(
            "identifier",
            |m: &Lens| { &m.identifier },
            |m: &mut Lens| { &mut m.identifier },
        ));
        ::protobuf::reflect::GeneratedMessageDescriptorData::new_2::<Lens>(
            "Lens",
            fields,
            oneofs,
        )
    }
}

impl ::protobuf::Message for Lens {
    const NAME: &'static str = "Lens";

    fn is_initialized(&self) -> bool {
        true
    }

    fn merge_from(&mut self, is: &mut ::protobuf::CodedInputStream<'_>) -> ::protobuf::Result<()> {
        while let Some(tag) = is.read_raw_tag_or_eof()? {
            match tag {
                10 => {
                    self.identifier = is.read_string()?;
                },
                tag => {
                    ::protobuf::rt::read_unknown_or_skip_group(tag, is, self.special_fields.mut_unknown_fields())?;
                },
            };
        }
        ::std::result::Result::Ok(())
    }

    // Compute sizes of nested messages
    #[allow(unused_variables)]
    fn compute_size(&self) -> u64 {
        let mut my_size = 0;
        if !self.identifier.is_empty() {
            my_size += ::protobuf::rt::string_size(1, &self.identifier);
        }
        my_size += ::protobuf::rt::unknown_fields_size(self.special_fields.unknown_fields());
        self.special_fields.cached_size().set(my_size as u32);
        my_size
    }

    fn write_to_with_cached_sizes(&self, os: &mut ::protobuf::CodedOutputStream<'_>) -> ::protobuf::Result<()> {
        if !self.identifier.is_empty() {
            os.write_string(1, &self.identifier)?;
        }
        os.write_unknown_fields(self.special_fields.unknown_fields())?;
        ::std::result::Result::Ok(())
    }

    fn special_fields(&self) -> &::protobuf::SpecialFields {
        &self.special_fields
    }

    fn mut_special_fields(&mut self) -> &mut ::protobuf::SpecialFields {
        &mut self.special_fields
    }

    fn new() -> Lens {
        Lens::new()
    }

    fn clear(&mut self) {
        self.identifier.clear();
        self.special_fields.clear();
    }

    fn default_instance() -> &'static Lens {
        static instance: Lens = Lens {
            identifier: ::std::string::String::new(),
            special_fields: ::protobuf::SpecialFields::new(),
        };
        &instance
    }
}

impl ::protobuf::MessageFull for Lens {
    fn descriptor() -> ::protobuf::reflect::MessageDescriptor {
        static descriptor: ::protobuf::rt::Lazy<::protobuf::reflect::MessageDescriptor> = ::protobuf::rt::Lazy::new();
        descriptor.get(|| file_descriptor().message_by_package_relative_name("Lens").unwrap()).clone()
    }
}

impl ::std::fmt::Display for Lens {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        ::protobuf::text_format::fmt(self, f)
    }
}

impl ::protobuf::reflect::ProtobufValue for Lens {
    type RuntimeType = ::protobuf::reflect::rt::RuntimeTypeMessage<Self>;
}

// @@protoc_insertion_point(message:spotify.lens.model.proto.LensState)
#[derive(PartialEq,Clone,Default,Debug)]
pub struct LensState {
    // message fields
    // @@protoc_insertion_point(field:spotify.lens.model.proto.LensState.identifier)
    pub identifier: ::std::string::String,
    // @@protoc_insertion_point(field:spotify.lens.model.proto.LensState.revision)
    pub revision: ::std::vec::Vec<u8>,
    // special fields
    // @@protoc_insertion_point(special_field:spotify.lens.model.proto.LensState.special_fields)
    pub special_fields: ::protobuf::SpecialFields,
}

impl<'a> ::std::default::Default for &'a LensState {
    fn default() -> &'a LensState {
        <LensState as ::protobuf::Message>::default_instance()
    }
}

impl LensState {
    pub fn new() -> LensState {
        ::std::default::Default::default()
    }

    fn generated_message_descriptor_data() -> ::protobuf::reflect::GeneratedMessageDescriptorData {
        let mut fields = ::std::vec::Vec::with_capacity(2);
        let mut oneofs = ::std::vec::Vec::with_capacity(0);
        fields.push(::protobuf::reflect::rt::v2::make_simpler_field_accessor::<_, _>(
            "identifier",
            |m: &LensState| { &m.identifier },
            |m: &mut LensState| { &mut m.identifier },
        ));
        fields.push(::protobuf::reflect::rt::v2::make_simpler_field_accessor::<_, _>(
            "revision",
            |m: &LensState| { &m.revision },
            |m: &mut LensState| { &mut m.revision },
        ));
        ::protobuf::reflect::GeneratedMessageDescriptorData::new_2::<LensState>(
            "LensState",
            fields,
            oneofs,
        )
    }
}

impl ::protobuf::Message for LensState {
    const NAME: &'static str = "LensState";

    fn is_initialized(&self) -> bool {
        true
    }

    fn merge_from(&mut self, is: &mut ::protobuf::CodedInputStream<'_>) -> ::protobuf::Result<()> {
        while let Some(tag) = is.read_raw_tag_or_eof()? {
            match tag {
                10 => {
                    self.identifier = is.read_string()?;
                },
                18 => {
                    self.revision = is.read_bytes()?;
                },
                tag => {
                    ::protobuf::rt::read_unknown_or_skip_group(tag, is, self.special_fields.mut_unknown_fields())?;
                },
            };
        }
        ::std::result::Result::Ok(())
    }

    // Compute sizes of nested messages
    #[allow(unused_variables)]
    fn compute_size(&self) -> u64 {
        let mut my_size = 0;
        if !self.identifier.is_empty() {
            my_size += ::protobuf::rt::string_size(1, &self.identifier);
        }
        if !self.revision.is_empty() {
            my_size += ::protobuf::rt::bytes_size(2, &self.revision);
        }
        my_size += ::protobuf::rt::unknown_fields_size(self.special_fields.unknown_fields());
        self.special_fields.cached_size().set(my_size as u32);
        my_size
    }

    fn write_to_with_cached_sizes(&self, os: &mut ::protobuf::CodedOutputStream<'_>) -> ::protobuf::Result<()> {
        if !self.identifier.is_empty() {
            os.write_string(1, &self.identifier)?;
        }
        if !self.revision.is_empty() {
            os.write_bytes(2, &self.revision)?;
        }
        os.write_unknown_fields(self.special_fields.unknown_fields())?;
        ::std::result::Result::Ok(())
    }

    fn special_fields(&self) -> &::protobuf::SpecialFields {
        &self.special_fields
    }

    fn mut_special_fields(&mut self) -> &mut ::protobuf::SpecialFields {
        &mut self.special_fields
    }

    fn new() -> LensState {
        LensState::new()
    }

    fn clear(&mut self) {
        self.identifier.clear();
        self.revision.clear();
        self.special_fields.clear();
    }

    fn default_instance() -> &'static LensState {
        static instance: LensState = LensState {
            identifier: ::std::string::String::new(),
            revision: ::std::vec::Vec::new(),
            special_fields: ::protobuf::SpecialFields::new(),
        };
        &instance
    }
}

impl ::protobuf::MessageFull for LensState {
    fn descriptor() -> ::protobuf::reflect::MessageDescriptor {
        static descriptor: ::protobuf::rt::Lazy<::protobuf::reflect::MessageDescriptor> = ::protobuf::rt::Lazy::new();
        descriptor.get(|| file_descriptor().message_by_package_relative_name("LensState").unwrap()).clone()
    }
}

impl ::std::fmt::Display for LensState {
    fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
        ::protobuf::text_format::fmt(self, f)
    }
}

impl ::protobuf::reflect::ProtobufValue for LensState {
    type RuntimeType = ::protobuf::reflect::rt::RuntimeTypeMessage<Self>;
}

static file_descriptor_proto_data: &'static [u8] = b"\
    \n\x10lens-model.proto\x12\x18spotify.lens.model.proto\"&\n\x04Lens\x12\
    \x1e\n\nidentifier\x18\x01\x20\x01(\tR\nidentifier\"G\n\tLensState\x12\
    \x1e\n\nidentifier\x18\x01\x20\x01(\tR\nidentifier\x12\x1a\n\x08revision\
    \x18\x02\x20\x01(\x0cR\x08revisionB0\n\x1ccom.spotify.lens.model.protoB\
    \x0eLensModelProtoH\x02b\x06proto3\
";

/// `FileDescriptorProto` object which was a source for this generated file
fn file_descriptor_proto() -> &'static ::protobuf::descriptor::FileDescriptorProto {
    static file_descriptor_proto_lazy: ::protobuf::rt::Lazy<::protobuf::descriptor::FileDescriptorProto> = ::protobuf::rt::Lazy::new();
    file_descriptor_proto_lazy.get(|| {
        ::protobuf::Message::parse_from_bytes(file_descriptor_proto_data).unwrap()
    })
}

/// `FileDescriptor` object which allows dynamic access to files
pub fn file_descriptor() -> &'static ::protobuf::reflect::FileDescriptor {
    static generated_file_descriptor_lazy: ::protobuf::rt::Lazy<::protobuf::reflect::GeneratedFileDescriptor> = ::protobuf::rt::Lazy::new();
    static file_descriptor: ::protobuf::rt::Lazy<::protobuf::reflect::FileDescriptor> = ::protobuf::rt::Lazy::new();
    file_descriptor.get(|| {
        let generated_file_descriptor = generated_file_descriptor_lazy.get(|| {
            let mut deps = ::std::vec::Vec::with_capacity(0);
            let mut messages = ::std::vec::Vec::with_capacity(2);
            messages.push(Lens::generated_message_descriptor_data());
            messages.push(LensState::generated_message_descriptor_data());
            let mut enums = ::std::vec::Vec::with_capacity(0);
            ::protobuf::reflect::GeneratedFileDescriptor::new_generated(
                file_descriptor_proto(),
                deps,
                messages,
                enums,
            )
        });
        ::protobuf::reflect::FileDescriptor::new_generated_2(generated_file_descriptor)
    })
}
